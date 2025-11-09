# Lil-Task-X

# Jira Auto-Assignment & Email Notification Script

This Python tool automates Jira issue creation and (optionally) sends assignment emails.  
It reads a structured JSON file representing sprints → features → user stories, then:

- Creates Jira issues  
- Assigns them to developers  
- Includes acceptance criteria in the description  
- Sends email notifications via SMTP  
- Supports dry-run mode (test without making real Jira changes)

 --- Jira ---
JIRA_BASE_URL=https://yourdomain.atlassian.net
JIRA_PROJECT_KEY=KAN
JIRA_ISSUE_TYPE=Task
JIRA_USERNAME=your_email@gmail.com
JIRA_API_TOKEN=YOUR_JIRA_API_TOKEN

 --- Email / SMTP ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=YOUR_GMAIL_APP_PASSWORD
EMAIL_FROM=your_email@gmail.com

 Optional: also CC yourself on every email
NOTIFY_EMAIL=your_email@gmail.com

pip install python-dotenv requests
source .env

echo $JIRA_BASE_URL
echo $JIRA_USERNAME

python3 connect_jira.py tasks.json --dry-run

python3 connect_jira.py tasks.json

python3 connect_jira.py tasks.json --send-emails

pip install requests python-dotenv

# JSON Input Format

The input file must follow this structure:

```json
{
  "sprints": [
    {
      "sprint_name": "Sprint 1: Authentication & UI",
      "features": [
        {
          "feature_name": "Login System",
          "stories": [
            {
              "summary": "Design login UI",
              "description": "Create login wireframe and React component",
              "acceptance_criteria": [
                "Form includes email + password fields",
                "Validation errors displayed on invalid input",
                "Login button disabled until input is valid"
              ],
              "assignee": {
                "name": "John Doe",
                "email": "john@example.com"
              },
              "labels": ["ui", "frontend"],
              "priority": "Medium"
            }
          ]
        }
      ]
    }
  ]
}


