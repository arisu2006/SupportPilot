"""
Enterprise Knowledge Base for SupportPilot.
In production this would be loaded from Confluence, SharePoint, ServiceNow, PDFs, etc.
"""

KNOWLEDGE_BASE = [
    {
        "id": "KB001",
        "title": "VPN Troubleshooting Guide",
        "category": "Network Connectivity",
        "content": """
Step-by-step instructions for resolving VPN connection issues.
1. Verify that the user has an active internet connection.
2. Check VPN client configuration and ensure the correct profile is selected.
3. Verify the VPN server address and port settings.
4. Verify authentication settings (username, password, MFA).
5. Restart the VPN service or client application.
6. Clear cached credentials if authentication fails.
7. Test connectivity from a different network to isolate the issue.
""",
    },
    {
        "id": "KB002",
        "title": "Network Firewall Configuration",
        "category": "IT Policies",
        "content": """
Corporate firewalls must allow VPN traffic.
Verify that VPN traffic is permitted on the required ports,
including ports 500 and 4500 for IPsec-based VPN connections.
Also ensure UDP 1194 is open for OpenVPN and TCP 443 for SSL VPN.
Contact the network security team if ports appear blocked.
""",
    },
    {
        "id": "KB003",
        "title": "VPN Authentication Problems",
        "category": "Authentication",
        "content": """
If VPN authentication fails, verify the username, password,
MFA configuration, cached credentials, and authentication
method configured in the VPN client.
Reset the user's MFA token if the authenticator app is out of sync.
Ensure the account is not locked after multiple failed attempts.
""",
    },
    {
        "id": "KB004",
        "title": "Password Reset Procedure",
        "category": "Authentication",
        "content": """
To reset a forgotten or expired password:
1. Navigate to the company self-service portal.
2. Select "Forgot Password" and enter the corporate email.
3. Complete MFA verification via registered phone or authenticator.
4. Set a new password meeting complexity requirements (min 12 chars, mixed case, number, symbol).
5. Wait 5 minutes for Active Directory replication before retrying login.
6. If self-service fails, open a Priority 3 ticket for helpdesk reset.
""",
    },
    {
        "id": "KB005",
        "title": "Outlook Email Sync Issues",
        "category": "Software",
        "content": """
When Outlook is not syncing emails:
1. Check internet connectivity and VPN status if remote.
2. Verify Exchange/Office 365 account credentials.
3. Restart Outlook in safe mode (outlook.exe /safe).
4. Clear the Outlook offline cache (.ost file) if corruption is suspected.
5. Repair the Office installation via Apps & Features.
6. Confirm mailbox size has not exceeded quota.
""",
    },
    {
        "id": "KB006",
        "title": "Hardware Peripheral Troubleshooting",
        "category": "Hardware",
        "content": """
For non-working keyboards, mice, monitors, or headsets:
1. Reseat the cable or try a different USB port.
2. Test the device on another computer to isolate hardware failure.
3. Update or reinstall the device driver from Device Manager.
4. For docking stations, update the dock firmware.
5. Check power management settings that may suspend USB devices.
6. Escalate to hardware replacement if the device fails on multiple machines.
""",
    },
    {
        "id": "KB007",
        "title": "System Performance and Blue Screen",
        "category": "System",
        "content": """
For slow systems, freezes, or blue screen errors:
1. Check Task Manager for high CPU/memory/disk usage.
2. Run Windows Memory Diagnostic and check Event Viewer for critical errors.
3. Update Windows and device drivers.
4. Scan for malware with the corporate endpoint protection tool.
5. Free disk space (aim for at least 15% free on system drive).
6. If BSOD persists, collect minidump files and escalate to Tier 2.
""",
    },
    {
        "id": "KB008",
        "title": "Shared Network Drive Access",
        "category": "Network Connectivity",
        "content": """
Unable to access shared network drives:
1. Confirm the user is connected to the corporate network or VPN.
2. Verify the share path (\\\\server\\share) is correct.
3. Check Active Directory group membership for the required share permissions.
4. Flush DNS cache (ipconfig /flushdns) and renew DHCP lease.
5. Map the drive again using the fully qualified domain name.
6. Contact storage team if the file server is unreachable from multiple users.
""",
    },
    {
        "id": "KB009",
        "title": "Software Installation and Licensing",
        "category": "Software",
        "content": """
For application installation or license issues:
1. Confirm the user has the correct license entitlement in the software catalog.
2. Use the corporate software center / SCCM / Intune for approved installs.
3. For license expiration, request renewal via the asset management portal.
4. Run the installer as administrator if permission errors occur.
5. Clear temporary files and retry if the installer fails mid-way.
6. Escalate to software asset management for volume license keys.
""",
    },
    {
        "id": "KB010",
        "title": "Two-Factor Authentication (MFA) Issues",
        "category": "Authentication",
        "content": """
When MFA codes are not received or rejected:
1. Verify the registered phone number or authenticator app is current.
2. Check that the device clock is synchronized (time drift breaks TOTP).
3. Request a new enrollment QR code from the identity portal if the token is lost.
4. Use backup codes if available.
5. Temporarily allow SMS fallback only after identity verification.
6. Escalate to Identity team for account unlock after repeated MFA failures.
""",
    },
]
