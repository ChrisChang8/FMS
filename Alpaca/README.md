# Alpaca connection notebook

Open [alpa-test.ipynb](notebooks/alpa-test.ipynb), select the repository's
`.venv` Python kernel, and run all cells in order.

From the repository root, install the existing development dependencies if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -e "./Simulated Engine[dev]"
```

The notebook reads `.env.local` from the repository root, with `env.local` as a
fallback. It works when the kernel starts in the root or the notebook directory.
Required variable names:

```dotenv
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_API_KEY_ID=your-key-id
ALPACA_API_SECRET_KEY=your-secret-key
```

Use the endpoint matching your key pair. The optional `/v2` URL suffix is accepted.
The file is read again on every run so stale kernel environment variables do not
override updated credentials.

The notebook makes three read-only checks:

1. Account authentication, showing only account status.
2. An authenticated AAPL quote request using IEX. Its timestamp can be from a
   previous session when the market is closed.
3. The original public Bitcoin daily-bar example, which does not test credentials.

No orders are placed. Credentials, account identifiers, and balances are not
printed. Clear notebook outputs before committing. HTTP 401 usually indicates a
key or paper/live endpoint mismatch; HTTP 403 indicates a permissions issue.

This is a standalone connectivity notebook, separate from the FMS simulator.
