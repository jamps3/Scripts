# PowerShell script to create a passwordless SSH login.

Script asks for:
```
user
hostname
port(optional)
```
it creates a SSH key (if it doesn't exist yet) and an alias (ssh *user*) for effortless SSH login.
