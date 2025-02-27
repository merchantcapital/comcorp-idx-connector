# mcauto-soap-client

## Removing permissions for .pem files

- Setting path variable: `$path = ".\private_key.pem"`

- Reset to remove explicit permissions: `icacls.exe $path /reset`

- Give current user explicit read-permission: `icacls.exe $path /GRANT:R "$($env:USERNAME):(R)"`

- Disablea inheritance and remove inherited permissions: `icacls.exe ./private_key.pem /inheritance:r`
 
