module.exports = {
  apps: [
    {
      name: "amesie_backend",
      script: "venv/bin/uvicorn",
      args: "main:app --host 0.0.0.0 --port 8001",
      cwd: "/root/amesie_backend",

      env_file: "/root/amesie_backend/.env",

      interpreter: "python3"
    }
  ]
};
