from src.transform import normalize_issue, to_tasks

def test_normalize_issue_minimal():
    issue = {
        "key": "TEST-1",
        "fields": {
            "project": {"key": "TEST"},
            "summary": "A title",
            "issuetype": {"name": "Bug"},
            "status": {"name": "Open"},
            "priority": {"name": "Major"},
            "assignee": {"displayName": "A"},
            "reporter": {"displayName": "B"},
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-02T00:00:00.000+0000",
            "description": "<p>Hello</p>"
        },
        "__comments": [{"body": "<p>Comment</p>"}]
    }
    norm = normalize_issue(issue)
    assert norm["key"] == "TEST-1"
    assert norm["project"] == "TEST"
    assert "Hello" in norm["description_text"]
    assert "Comment" in norm["comments_text"][0]

def test_tasks_present():
    issue = {
        "key": "X-1",
        "fields": {"summary": "Title"},
        "__comments": []
    }
    norm = {
        "title": "Title",
        "description_text": "Desc",
        "comments_text": []
    }
    tasks = to_tasks(norm)
    assert any(t["task"] == "summarization" for t in tasks)
