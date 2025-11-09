import json
import os
import requests
import smtplib
from email.mime.text import MIMEText
import argparse
import logging

# --- Jira + Email Config ---
JIRA_BASE_URL   = os.getenv("JIRA_BASE_URL", "https://jasleenkaurbhui.atlassian.net")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY") 
JIRA_ISSUE_TYPE  = os.getenv("JIRA_ISSUE_TYPE", "Task")
JIRA_USERNAME   = os.getenv("JIRA_USERNAME", "jasleen.kaur.bhui@gmail.com")
JIRA_API_TOKEN  = os.getenv("JIRA_API_TOKEN", "ATATT3xFfGF0O6_QlElbe3E3bj6TkQN7pTV_mpG2L0Rm6WW5uxV9Deu--sXLz_14D_lWSTuhk6zuVcKWs3YYRo0iHiHyZLYUnikl9xWshBIGK-kH7U0E78XgDsTHQXfLKiru-PAu9lIyYVr-oy9VxM2vrccPCFJe0NlGxu-nu1FnkAT0MS_uG60=83DD7C9E")

SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME   = os.getenv("SMTP_USERNAME", "jasleen.kaur.bhui@gmail.com")
SMTP_PASSWORD   = os.getenv("SMTP_PASSWORD")
EMAIL_FROM      = os.getenv("EMAIL_FROM", SMTP_USERNAME)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto-assign")

# --- Helpers ---
def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def create_jira_issue(summary, description, assignee_email, labels=None, priority="Medium", dry_run=True):
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": JIRA_ISSUE_TYPE},
            "priority": {"name": priority},
            "labels": labels or []
        }
    }

    if dry_run:
        logger.info("[DRY RUN] Would create Jira issue:")
        logger.info(json.dumps(payload, indent=2))
        return {"key": "DRY-RUN-123"}

    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    resp = requests.post(
        url,
        auth=(JIRA_USERNAME, JIRA_API_TOKEN),
        headers={"Content-Type": "application/json"},
        json=payload
    )

    if resp.status_code in (200, 201):
        issue_key = resp.json().get("key", "UNKNOWN")
        logger.info(f"Created Jira issue: {issue_key}")
        return resp.json()
    else:
        logger.error(f"Failed to create Jira issue: {resp.status_code} {resp.text}")
        return None


def send_email(to_email, subject, body, dry_run=True):
    if dry_run:
        logger.info(f"[DRY RUN] Would send email to {to_email}")
        logger.info(body)
        return

    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    # Add yourself as an additional recipient
    recipients = [to_email, os.getenv("NOTIFY_EMAIL", SMTP_USERNAME)]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(EMAIL_FROM, recipients, msg.as_string())
    server.quit()
    logger.info(f"Email sent to {', '.join(recipients)}")

# --- Main Assignment Logic ---
def assign_tasks(json_data, dry_run=True, send_emails=False):
    sprints = json_data["sprints"]

    for sprint in sprints:
        logger.info(f"\n Processing: {sprint['sprint_name']}")
        for feature in sprint["features"]:
            for story in feature["stories"]:

                summary = story["summary"]
                description = story["description"] + "\n\nAcceptance Criteria:\n"
                for ac in story["acceptance_criteria"]:
                    description += f"- {ac}\n"

                assignee_email = story["assignee"]["email"]
                labels = story.get("labels", [])
                priority = story.get("priority", "Medium")

                # Create Jira Issue
                issue = create_jira_issue(
                    summary,
                    description,
                    assignee_email,
                    labels=labels,
                    priority=priority,
                    dry_run=dry_run
                )

                # Send Email if enabled
                if send_emails:
                    body = f"You have been assigned a new Jira task:\n\n{summary}\n\nCheck Jira for more details."
                    send_email(assignee_email, f"New Task: {summary}", body, dry_run=dry_run)

    logger.info("\n Finished assigning all tasks")


# --- CLI Entry ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send-emails", action="store_true")
    args = parser.parse_args()

    data = load_json(args.json_file)
    assign_tasks(data, dry_run=args.dry_run, send_emails=args.send_emails)
