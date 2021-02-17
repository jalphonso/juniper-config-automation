import os
import sys
import base64
import gitlab

from flask import Flask, request, Response
from secrets import (TOKENS, ACTIONS, GITLAB_TOKEN, GITLAB_URL,
                    SSH_USER, SSH_PRIVATE_KEY_PATH)
from jnpr.junos import Device
from gitlab.exceptions import GitlabError

app = Flask(__name__)


def backup_config(server, comment=None):
    print(f"Backing up config for device {server}...")

    # Retrieve config from device
    device_config = None

    try:
        with Device(host=server, user=SSH_USER, ssh_private_key_file=SSH_PRIVATE_KEY_PATH) as dev:
            device_config = dev.rpc.get_config(options={'database' : 'committed',
                                            'format': 'text'}).text
    except Exception as e:
        print(e)

    if not device_config:
        print(f"Unable to get config for device {server}")
        print("Backup unsucccessful")
        return

    if comment:
        message = comment.split("UI_COMMIT:")[1]
    else:
        message = "Updated Config"

    # GITLAB AUTH
    gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_TOKEN)
    gl.auth()

    # Retrieve existing device config and update it
    project = gl.projects.list(search="network_configs")[0]
    try:
        f = project.files.get(file_path=server, ref='master')
        if f.content.encode("utf-8") != base64.b64encode(device_config.encode("utf-8")):
            f.content = device_config
            f.save(branch='master', commit_message=f'{server}: {message}')
            print(f"Saved config change for {server} in Gitlab")
        else:
            print(f"No configuration change for device {server}. Skipping commit...")

    # If device config does not exist create it
    except GitlabError:
        f = project.files.create({'file_path': server,
                          'branch': 'master',
                          'content': device_config,
                          'author_email': '',
                          'author_name': 'project_bot',
                          'commit_message': f'{server}: {message}'})
    print("Backup complete")


@app.route('/backup', methods=['POST'])
def backup():
    try:
        print(request.json)
        token = request.json['token']
        action = request.json['action']

        if token in TOKENS:
            print(f"Token {token} was used")
        else:
            print(f"Invalid Token: {token}")
            return Response(status=401)

        if action not in ACTIONS:
            print(f"Unsupported action: {action}")
            raise Exception

        print(f"User wants to execute the following action: {action}")
        if action == "backup":
            backup_config(request.json['server'], request.json['comment'])
        return Response(status=200)
    except Exception:
        print("Did you provide all the required json fields?")
        return Response(status=400)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
