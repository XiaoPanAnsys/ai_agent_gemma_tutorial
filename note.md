## Get Started
1. Prepare python3 env :
    ```sh
    python3 -m venv gemma-env
    source gemma-env/bin/
    pip install --upgrade pip  # update pip
    pip install -r requirements.txt # install requirements
    ```

2. Install ollama  `curl -fsSL https://ollama.com/install.sh | sh`

    check version `ollama --version , ollama -h`

    Uninstall:
    ```
    sudo systemctl stop ollama
    sudo systemctl disable ollama
    sudo rm -f /etc/systemd/system/ollama.service
    sudo rm -f /usr/local/bin/ollama
    sudo rm -rf /usr/share/ollama
    sudo rm -rf ~/.ollama
    sudo systemctl daemon-reload
    ```


3. Pull LLVm model `ollama pull gemma3:4b`
    ```bash
    (gemma-env) xiaopan@AAPL1Ltv1Xq1msn:~/personal/AI_Agent_Gemma$ ollama pull gemma3:4b
    pulling manifest
    pulling aeda25e63ebd: 100% ▏ 3.3 GB
    pulling e0a42594d802: 100% ▏  358 B
    pulling dd084c7d92a3: 100%  8.4 KB
    pulling 3116c5225075: 100% ▏   77 B
    pulling b6ae5839783f: 100%   489 B
    verifying sha256 digest
    writing manifest
    success
    ```


4. Start Ollama Server : `ollama serve`, the server runs at port `11434`

   my note created from the console
    ```
    Couldn't find '/home/xiaopan/.ollama/id_ed25519'. Generating new private key.
    Your new public key is:
    ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKs0otcu+golxOOHz6qxH1dDS9fWw/six6OkOhClMpbS
    Error: listen tcp 127.0.0.1:11434: bind: address already in use
    ```

    Check if it is running `curl http://localhost:11434/api/tags` ->  you’ll get JSON output listing installed models.

5. Try first command, see file `Ex_Files_Create_AI_Agent_Gemma/curl_command.txt`:
   ```bash
   curl -X POST http://localhost:11434/api/generate  -d '{"model": "gemma3:4b", "prompt": "Why is the sky blue?", "stream": false}'
   ```

6. Try Ollam, using request lib, post API : `Ex_Files_Create_AI_Agent_Gemma/ollama_test.py`
   ```bash
   python3 Ex_Files_Create_AI_Agent_Gemma/ollama_test.py
   ```

---

BUild 
