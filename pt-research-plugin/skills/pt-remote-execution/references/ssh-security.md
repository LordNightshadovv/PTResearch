# SSH security boundary

Use the existing `~/.ssh/config` alias (for example `pt-linux`) and ordinary OpenSSH. The recommended dedicated key is `~/.ssh/pt_simulation_ed25519`, permission `0600`, with its public key `0644`; `~/.ssh` is `0700` and config is `0600`. Generate and add it to the macOS agent/Keychain only after approval: `ssh-keygen -t ed25519 -f ~/.ssh/pt_simulation_ed25519 -C "PT simulation access"` then `ssh-add --apple-use-keychain ~/.ssh/pt_simulation_ed25519`.

The plugin may check existence, mode, public fingerprint, and `ssh-add -l`, but never reads, prints, logs, uploads, or packages private-key material. The Linux public key is in `~/.ssh/authorized_keys` with `0700/.ssh` and `0600/authorized_keys`. Test key login before disabling password login. Compare the Linux Ed25519 host-key fingerprint out of band before first trust; an unexpected changed key is blocking.

Use ordinary OpenSSH over LAN or an approved mesh VPN such as Tailscale. Do not expose port 22 publicly by default, enable Tailscale SSH automatically, weaken host verification, or alter firewall/router/VPN/sshd settings without explicit approval.
