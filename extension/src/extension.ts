// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "DocHelper" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('DocHelper.helloWorld', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		// vscode.window.showInformationMessage('Hello World from ai-doc-helper!!!!');

		const panel = vscode.window.createWebviewPanel(
			'aiDocHelper',
			'AI Doc Helper',
			vscode.ViewColumn.Beside,
			{ enableScripts: true }
		);

		// set the HTML
    	panel.webview.html = getWebviewHtml();

		function getWebviewHtml(): string {
			const nonce = getNonce();
			return `<!DOCTYPE html>
			<html lang="en">
			<head>
				<meta charset="UTF-8">
				<!-- Allow script (nonce) + XHR/fetch to backend -->
				<meta http-equiv="Content-Security-Policy"
				content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src http://127.0.0.1:8000;">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>AI Doc Helper</title>
				<style>
				body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; padding: 20px; }
				.card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; max-width: 560px; }
				.row { margin-top: 12px; }
				button { padding: 8px 12px; border-radius: 8px; border: 1px solid #e5e7eb; cursor: pointer; }
				code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
				</style>
			</head>
			<body>
				<div class="card">
				<h2>Hello AI Docs 👋</h2>
				<p>This panel can now talk to a local FastAPI backend.</p>

				<div class="row">
					<button id="ping">Ping Backend</button>
					<span id="status" style="margin-left:10px;color:#6b7280;">(idle)</span>
				</div>

				<pre id="result" class="row"></pre>
				</div>

				<script nonce="${nonce}">
				const pingBtn = document.getElementById('ping');
				const statusEl = document.getElementById('status');
				const resultEl = document.getElementById('result');

				async function ping() {
					statusEl.textContent = 'contacting http://127.0.0.1:8000/health ...';
					resultEl.textContent = '';
					try {
					const res = await fetch('http://127.0.0.1:8000/health');
					const json = await res.json();
					statusEl.textContent = res.ok ? '✓ online' : '✗ error';
					resultEl.textContent = JSON.stringify(json, null, 2);
					} catch (e) {
					statusEl.textContent = '✗ failed';
					resultEl.textContent = String(e);
					}
				}

				pingBtn.addEventListener('click', ping);
				</script>
			</body>
			</html>`;
		}

		function getNonce() {
			const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
			let s = '';
			for (let i = 0; i < 32; i++) s += chars.charAt(Math.floor(Math.random() * chars.length));
			return s;
		}
	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
