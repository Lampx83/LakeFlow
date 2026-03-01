import { DocPage } from "@/components/docs/DocPage";

export default function DeploymentPage() {
  return (
    <DocPage
      title="Deployment"
      prevHref="/docs/configuration"
      prevLabel="Configuration"
    >
      <h2>Portainer Stack</h2>
      <p>Portainer does not support <code>build</code> in stack. Build and push images to Docker Hub first.</p>
      <h3>Step 1: Build and push images</h3>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`cd LakeFlow
export DOCKERHUB_USER=your-username
DOCKER_BUILDKIT=1 docker build -t $DOCKERHUB_USER/lakeflow-backend:latest ./backend
docker build -t $DOCKERHUB_USER/lakeflow-frontend:latest ./frontend/streamlit
docker push $DOCKERHUB_USER/lakeflow-backend:latest
docker push $DOCKERHUB_USER/lakeflow-frontend:latest`}
      </pre>
      <h3>Step 2: Create stack in Portainer</h3>
      <ol className="list-decimal pl-5 mt-2 space-y-1">
        <li>Portainer → Stacks → Add stack</li>
        <li>Web editor → paste contents of <code>portainer-stack.yml</code></li>
        <li>Env vars: add <code>DOCKERHUB_USER</code> (e.g. lampx83). Can add other vars from <code>.env</code> if needed.</li>
        <li>Deploy stack</li>
      </ol>
      <p className="mt-2"><strong>Note:</strong> Stack uses named volume <code>lakeflow_data</code>. For host path bind, edit stack to add <code>driver_opts</code> with <code>device: /path/on/host</code> for volume.</p>

      <h2>Manual deploy to server</h2>
      <p>On VPS or on-prem (Ubuntu, Debian...):</p>
      <ol className="list-decimal pl-5 mt-2 space-y-2">
        <li>Clone and prepare env:</li>
      </ol>
      <pre className="code-block mt-2 overflow-x-auto rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-mono text-sm text-brand-400">
{`git clone https://github.com/Lampx83/LakeFlow.git
cd LakeFlow
cp env.example .env
nano .env   # Edit HOST_LAKE_PATH, QDRANT_HOST, API_BASE_URL, LLM_BASE_URL...`}
      </pre>
      <ol className="list-decimal pl-5 mt-2 space-y-1" start={2}>
        <li>Create Data Lake directory: <code>mkdir -p $HOST_LAKE_PATH/000_inbox $HOST_LAKE_PATH/100_raw $HOST_LAKE_PATH/200_staging $HOST_LAKE_PATH/300_processed $HOST_LAKE_PATH/400_embeddings $HOST_LAKE_PATH/500_catalog</code></li>
        <li>Run: <code>DOCKER_BUILDKIT=1 docker compose up -d --build</code></li>
      </ol>
      <p className="mt-2">Using deploy override (fixed bind mount): <code>export LAKEFLOW_DATA_PATH=/datalake/research</code> then <code>docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build</code></p>

      <h2>Auto deploy (GitHub Actions)</h2>
      <p>Workflow <code>.github/workflows/deploy.yml</code> SSHs to server and runs <code>docker compose</code> on each push to <code>main</code>.</p>
      <h3>Server setup (one-time)</h3>
      <ol className="list-decimal pl-5 space-y-2">
        <li><strong>Install Docker:</strong>
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and log back in`}</pre>
        </li>
        <li><strong>Clone repo:</strong> <code>cd ~ &amp;&amp; git clone https://github.com/Lampx83/LakeFlow.git lakeflow</code></li>
        <li><strong>Create .env:</strong> <code>cp env.example .env</code> (or <code>cp .env.example .env</code>) then edit <code>LAKE_ROOT</code>, <code>QDRANT_HOST</code>, <code>API_BASE_URL</code></li>
        <li><strong>Create Data Lake directory:</strong> <code>sudo mkdir -p /datalake/research &amp;&amp; sudo chown $USER:$USER /datalake/research</code></li>
        <li><strong>SSH key for GitHub Actions:</strong>
          <pre className="mt-1 overflow-x-auto rounded border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-brand-400">{`ssh-keygen -t ed25519 -C "deploy" -f ~/.ssh/deploy_lakeflow -N ""
cat ~/.ssh/deploy_lakeflow.pub >> ~/.ssh/authorized_keys
# Get private key: cat ~/.ssh/deploy_lakeflow → paste into GitHub Secret SSH_PRIVATE_KEY`}</pre>
        </li>
      </ol>
      <h3>GitHub Secrets</h3>
      <p>Settings → Secrets and variables → Actions → New repository secret:</p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr>
            <th>Secret</th>
            <th>Required</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>DEPLOY_HOST</code></td><td>Yes</td><td>Server IP or hostname (e.g. 123.45.67.89)</td></tr>
          <tr><td><code>DEPLOY_USER</code></td><td>Yes</td><td>SSH user (e.g. ubuntu)</td></tr>
          <tr><td><code>SSH_PRIVATE_KEY</code></td><td>Yes</td><td>Full private key content (including BEGIN/END)</td></tr>
          <tr><td><code>DEPLOY_REPO_DIR</code></td><td>No</td><td>Repo directory on server; default <code>~/lakeflow</code></td></tr>
          <tr><td><code>DEPLOY_SSH_PORT</code></td><td>No</td><td>SSH port if not 22</td></tr>
        </tbody>
      </table>

      <h2>Data Lake mount</h2>
      <ul>
        <li><strong>Docker Compose (dev):</strong> Uses <code>HOST_LAKE_PATH</code> from <code>.env</code>. Directory must exist.</li>
        <li><strong>docker-compose.deploy.yml:</strong> Volume bind <code>LAKEFLOW_DATA_PATH</code> (default <code>./data</code>). On server: <code>export LAKEFLOW_DATA_PATH=/datalake/research</code> before running compose.</li>
      </ul>

      <h2>CI/CD</h2>
      <table className="mt-2 w-full text-sm">
        <thead><tr><th>Workflow</th><th>Trigger</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td><code>ci.yml</code></td><td>Push/PR main, develop</td><td>Lint (Ruff), Docker build</td></tr>
          <tr><td><code>cd.yml</code></td><td>Release tag</td><td>Build + push images to GitHub Container Registry</td></tr>
          <tr><td><code>push-dockerhub.yml</code></td><td>Push main (when backend/frontend changed)</td><td>Push lakeflow-backend, lakeflow-frontend to Docker Hub. Needs DOCKERHUB_USER, DOCKERHUB_TOKEN</td></tr>
          <tr><td><code>publish-pypi.yml</code></td><td>GitHub Release</td><td>Publish <code>lake-flow-pipeline</code> to PyPI</td></tr>
          <tr><td><code>deploy.yml</code></td><td>Push main</td><td>SSH → git pull → docker compose up</td></tr>
        </tbody>
      </table>
    </DocPage>
  );
}
