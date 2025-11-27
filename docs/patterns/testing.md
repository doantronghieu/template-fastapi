# Testing Patterns

## API Client Testing with Bruno

[Bruno](https://www.usebruno.com/) - Git-friendly, offline-first API client storing requests as plain text.

### Structure

- **`bruno.json`** - Collection metadata
- **`collection.bru`** - Shared settings
- **`environments/local.bru`** - Variables (`vars {}` block)
- **`{feature}/*.bru`** - One request per file, grouped by feature

### Usage

1. Open `bruno/` folder as collection
2. Select environment (e.g., "local") from dropdown
3. Update `environments/local.bru` with actual values
4. Execute requests individually or by folder

### Conventions

- **Naming**: kebab-case files (`get-users.bru`, `create-order.bru`)
- **Variables**: Define in environment file, reference as `{{varName}}`
- **Credentials**: Use placeholders, never commit real values
- **Organization**: Group by feature (`auth/`, `users/`, `validation-errors/`)

---