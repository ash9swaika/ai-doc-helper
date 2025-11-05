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

		panel.webview.html = `
			<!DOCTYPE html>
			<html lang="en">
			<head>
			<meta charset="UTF-8">
			<title>AI Doc Helper</title>
			<style>
			body {
				font-family: sans-serif;
				padding: 20px;
			}
			</style>
			</head>
			<body>
			<h2>Hello AI Docs 👋</h2>
			<p>This is your static webview panel.</p>
			</body>
			</html>`;

	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
