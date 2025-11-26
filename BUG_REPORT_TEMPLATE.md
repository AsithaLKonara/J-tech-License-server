# Bug Report Template

Use this template when reporting bugs found during testing.

---

## Bug Information

**Bug ID:** BUG-XXXX  
**Title:** [Brief, descriptive title]  
**Severity:** 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low  
**Priority:** P0 / P1 / P2 / P3  
**Component:** Design Tools Tab / Preview Tab / Flash Tab / Other  
**Test Case:** TC-UX-XXX (if applicable)  
**Reporter:** [Your Name]  
**Date Reported:** YYYY-MM-DD  
**Status:** New / In Progress / Fixed / Verified / Closed

---

## Description

[Clear, concise description of the bug]

---

## Steps to Reproduce

1. [Step 1]
2. [Step 2]
3. [Step 3]
4. ...

**Reproducibility:** Always / Sometimes / Rarely / Once

---

## Expected Result

[What should happen]

---

## Actual Result

[What actually happens]

---

## Environment

- **OS:** Windows 10 / macOS 12.x / Linux (Ubuntu 22.04) / Other
- **Python Version:** 3.10.x / 3.11.x / 3.12.x
- **Application Version:** 3.0.0
- **Qt Version:** [if known]
- **Hardware:** [if relevant]

---

## Screenshots/Logs

[Attach screenshots, error messages, or log files]

```
[Paste error logs here]
```

---

## Additional Information

- **Related Bugs:** BUG-XXXX, BUG-YYYY
- **Workaround:** [If any]
- **Impact:** [How many users affected, severity of impact]
- **Notes:** [Any other relevant information]

---

## Developer Notes

[For developers - leave blank when reporting]

**Assigned To:** [Developer Name]  
**Estimated Fix Time:** [Hours/Days]  
**Fix Commit:** [Commit hash]  
**Verification Date:** YYYY-MM-DD

---

## Example Bug Report

**Bug ID:** BUG-0001  
**Title:** Pattern loading fails silently when file is corrupted  
**Severity:** 🔴 Critical  
**Priority:** P0  
**Component:** Design Tools Tab  
**Test Case:** TC-UX-001

**Description:**  
When loading a corrupted pattern file, the application fails silently without showing any error message to the user. The user is left confused about why the file didn't load.

**Steps to Reproduce:**
1. Open Design Tools tab
2. Click "Open" button
3. Select a corrupted pattern file (e.g., `corrupted_pattern.dat`)
4. Observe application behavior

**Expected Result:**  
Error dialog appears with message: "Failed to load pattern file. The file may be corrupted or in an unsupported format."

**Actual Result:**  
No error dialog appears. The file dialog closes and nothing happens. The pattern remains unchanged.

**Environment:**
- OS: Windows 10
- Python Version: 3.11.5
- Application Version: 3.0.0

**Screenshots/Logs:**
[Attach screenshot of file dialog or error log]

**Impact:**  
High - Users cannot understand why files won't load, leading to frustration and support requests.

---

**Template Version:** 1.0  
**Last Updated:** 2025-01-XX

