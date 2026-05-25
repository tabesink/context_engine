# 5. ASCII Screens by API Surface

## 5.1 Session Login Screen

Success screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Login                                                        │
│ API Group: auth                                              │
├──────────────────────────────────────────────────────────────┤
│ Summary                                                      │
│  backend: http://127.0.0.1:8000                              │
│  email: admin@example.com                                    │
│  status: success                                             │
│                                                              │
│ Saved session                                                │
│ +----------------+---------------------------+               │
│ | field          | value                     |               │
│ +----------------+---------------------------+               │
│ | API base URL   | http://127.0.0.1:8000     |               │
│ | Token stored   | yes                       |               │
│ | Password saved | no                        |               │
│ +----------------+---------------------------+               │
│                                                              │
│ Next actions                                                 │
│  [1] Current session   ragcli auth me                        │
│  [2] Documents         ragcli documents list                 │
└──────────────────────────────────────────────────────────────┘
```
[question] What does the current session show, what is it? what's it purpose? Do each user logged into the system get a current session, when does it expire? I need to understand what this "session" is
