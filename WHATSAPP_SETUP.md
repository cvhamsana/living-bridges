# WhatsApp integration checklist

The starter includes the webhook verification route and an inbound placeholder only. To make the flow live:

1. Create/configure a Meta developer app and WhatsApp Cloud API test number.
2. Set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN` in `backend/.env`.
3. Expose FastAPI over HTTPS for webhook testing (ngrok may be used during development).
4. Configure the callback URL and verification token in Meta.
5. Implement signature verification and parse incoming messages/media IDs.
6. Download media using the current Meta Graph API requirements, validate size/type, and pass media to the same recognition pipeline.
7. Send a menu reply with options:
   - Identify an unknown dog
   - Register a known new dog
   - Update an existing dog record
8. Implement outbound messages and media download with error handling and rate limits.
9. Add consent, retention rules, access controls, masked contact handling and audit logs.
10. Test in the approved pilot before sharing with volunteers.

Do not commit real tokens to GitHub. Meta free-tier limits and requirements can change; verify current official documentation before deployment.
