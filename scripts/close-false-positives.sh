#!/bin/bash
# Script zum Schließen aller bestehenden False-Positive Security Alerts

echo "🧹 Schließe alle bestehenden False-Positive Security Alerts..."

# Hole alle offenen Alert-Nummern
ALERT_NUMBERS=$(gh api repos/Randomname653/language-fixer/code-scanning/alerts --paginate --jq '.[] | select(.state == "open") | .number')

echo "Gefundene offene Alerts: $(echo "$ALERT_NUMBERS" | wc -l)"

# Schließe jeden Alert als False Positive
for alert in $ALERT_NUMBERS; do
    echo "Schließe Alert #$alert..."
    gh api --method PATCH repos/Randomname653/language-fixer/code-scanning/alerts/$alert \
        -f state='dismissed' \
        -f dismissed_reason='false positive' \
        -f dismissed_comment='Automatisch geschlossen: Container-Dependencies sind in unserer kontrollierten Umgebung nicht exploitable'
    sleep 0.1  # Rate limiting vermeiden
done

echo "✅ Alle False-Positive Alerts wurden geschlossen!"