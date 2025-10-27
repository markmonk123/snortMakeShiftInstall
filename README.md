# snortMakeShiftInstall
A python executable to install snort3 the networking application and then configure it for IDS/IPS

## Environment configuration

Copy `.env.example` to `.env` (or export the variables manually) and populate the real values before launching the container:

```
cp .env.example .env
```

At minimum you must set `ML_API_KEY` to your OpenAI API key. The startup scripts also accept `OPENAI_API_KEY` as an alias. When either variable is present, the entrypoint will run `setup_openai_api.sh --auto` to generate `/etc/snort/ml_runner/api_config.json` and `ml_runner.env` inside the container.

## Self-hosted runner workflow

The repository ships with a `Self-Hosted Runner Ping` workflow (`.github/workflows/self-hosted-runner-ping.yml`) that targets the `self-hosted`/`snort-runner` labels. Trigger it via **Actions → Self-Hosted Runner Ping → Run workflow** to send a message payload to the runner, capture context such as `RUNNER_NAME`, and upload the resulting log as an artifact.
