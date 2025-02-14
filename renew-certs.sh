#!/bin/bash

# ============================================================================
# Description:
#   This script performs the following actions:
#     1. Checks for and creates (if necessary) the webroot directory for certificates.
#     2. Sets proper ownership and permissions for the webroot directory.
#     3. Checks for the presence of certificates for the specified domains.
#         - If certificates are not found, it creates new ones using certbot.
#         - If certificates exist, it checks whether renewal is necessary.
#     4. Reloads Nginx to apply the new certificates.
#     5. If certificates are successfully created or renewed, it installs a cron job
#        to run this script daily at midnight.
#
# Requirements:
#   - The script must be run as root.
#   - certbot and Nginx must be installed.
#
# Usage:
#   Run the script manually or let the installed cron job execute it daily.
#
# ============================================================================

LOG_FILE="/var/log/certbot-update.log"

SCRIPT_PATH=$(readlink -f "$0")

CRON_JOB="0 0 * * * $SCRIPT_PATH"

WEBROOT="/var/www/html"

DOMAINS=("example.com" "www.example.com")  # TODO: Replace with your actual domains

EMAIL="example@example.com" # TODO: Replace with your actual email


log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}


if [[ "$EUID" -ne 0 ]]; then
    log "Script should be run as root."
    exit 1
fi

log "=== Starting the certificate creation/renewal process ==="

if [ ! -d "$WEBROOT" ]; then
    log "Webroot directory $WEBROOT does not exist. Creating it."
    mkdir -p "$WEBROOT"
    if [[ $? -ne 0 ]]; then
        log "Failed to create webroot directory $WEBROOT."
        exit 1
    fi

    log "Setting ownership of $WEBROOT to www-data:www-data."
    chown -R www-data:www-data "$WEBROOT"
    if [[ $? -ne 0 ]]; then
        log "Failed to set ownership for $WEBROOT."
        exit 1
    fi

    log "Setting permissions of $WEBROOT to 755."
    chmod -R 755 "$WEBROOT"
    if [[ $? -ne 0 ]]; then
        log "Failed to set permissions for $WEBROOT."
        exit 1
    fi
else
    log "Webroot directory $WEBROOT already exists. Ensuring correct ownership and permissions."

    CURRENT_OWNER=$(stat -c "%U:%G" "$WEBROOT")
    if [[ "$CURRENT_OWNER" != "www-data:www-data" ]]; then
        log "Incorrect ownership ($CURRENT_OWNER) for $WEBROOT. Setting to www-data:www-data."
        chown -R www-data:www-data "$WEBROOT"
        if [[ $? -ne 0 ]]; then
            log "Failed to set ownership for $WEBROOT."
            exit 1
        fi
    else
        log "Ownership for $WEBROOT is correctly set to www-data:www-data."
    fi

    CURRENT_PERMS=$(stat -c "%a" "$WEBROOT")
    if [[ "$CURRENT_PERMS" != "755" ]]; then
        log "Incorrect permissions ($CURRENT_PERMS) for $WEBROOT. Setting to 755."
        chmod -R 755 "$WEBROOT"
        if [[ $? -ne 0 ]]; then
            log "Failed to set permissions for $WEBROOT."
            exit 1
        fi
    else
        log "Permissions for $WEBROOT are correctly set to 755."
    fi
fi

CERT_PATH="/etc/letsencrypt/live/${DOMAINS[0]}"

if [ ! -d "$CERT_PATH" ]; then
    log "Certificates for domains ${DOMAINS[*]} not found. Starting the creation of new certificates."

    certbot certonly --webroot \
        -w "$WEBROOT" \
        $(for domain in "${DOMAINS[@]}"; do echo -n "-d $domain "; done) \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        >> "$LOG_FILE" 2>&1

    if [[ $? -eq 0 ]]; then
        log "Certificates successfully created for domains ${DOMAINS[*]}."
    else
        log "Error occurred while creating certificates for domains ${DOMAINS[*]}. Check the logs for details."
        exit 1
    fi
else
    log "Certificates for domains ${DOMAINS[*]} already exist. Checking if renewal is necessary."

    certbot renew --webroot -w "$WEBROOT" --preferred-challenges http \
        --post-hook "systemctl reload nginx" \
        >> "$LOG_FILE" 2>&1

    if [[ $? -eq 0 ]]; then
        log "Certificates successfully renewed for domains ${DOMAINS[*]}."
    else
        log "Error occurred while renewing certificates for domains ${DOMAINS[*]}. Check the logs for details."
        exit 1
    fi
fi

log "Reloading Nginx to apply the certificates."
systemctl reload nginx
if [[ $? -eq 0 ]]; then
    log "Nginx reloaded successfully."
else
    log "Error occurred while reloading Nginx."
    exit 1
fi

if [ -d "$CERT_PATH" ]; then
    log "Certificates are present at $CERT_PATH. Proceeding to install cron job."

    if crontab -l 2>/dev/null | grep -Fq "$SCRIPT_PATH"; then
        log "Cron job already exists for $SCRIPT_PATH. Skipping cron installation."
    else
        log "Installing cron job to run this script."
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        if [[ $? -eq 0 ]]; then
            log "Cron job installed successfully."
        else
            log "Failed to install cron job."
        fi
    fi
else
    log "Certificates directory $CERT_PATH not found. Skipping cron job installation."
fi

log "=== Certificate creation/renewal process completed successfully ==="
exit 0
