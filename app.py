import gitlab
import ollama
import os
from dotenv import load_dotenv
load_dotenv()

GITLAB_URL = os.getenv("GITLAB_URL")
TOKEN = os.getenv("GITLAB_TOKEN")
MODELO_OLLAMA = 'reviewer'

gl = gitlab.Gitlab(GITLAB_URL, private_token=TOKEN)

mrs = gl.mergerequests.list(
    assignee_username='joao.demeto',
    state='opened',
    scope='all',
    get_all=True
)

for mr_summary in mrs:
    skip = False
    project = gl.projects.get(mr_summary.project_id)
    mr = project.mergerequests.get(mr_summary.iid)
    notes = mr.notes.list(get_all=True)
    for note in notes:
        if "Ollama" in note.body:
            skip = True
    
    if skip:
        continue
            
    print(f"\nAnalisando e comentando no MR #{mr.iid}...")

    changes_data = mr.changes()
    full_review = "**Ollama Code Review**\n\n"
    for change in changes_data['changes']:
        file_path = change['new_path']
        print(f"Processando {file_path}")
        title = changes_data['title']
        description = changes_data['description']

        if not any(file_path.endswith(ext) for ext in ['.php', '.py', '.sql']):
            continue

        diff_content = change['diff']

        response = ollama.chat(
            model=MODELO_OLLAMA,
            messages=[
                {
                    "role": "user",
                    "content": f"""
        Review this GitLab merge request diff.

        ### FILE
        {file_path}

        ### TITLE
        {title}

        ### INSTRUCTIONS
        - Focus ONLY on added (+) and removed (-) lines
        - Ignore unchanged context
        - Be concise
        - Do not explain basics

        ### DIFF
        {diff_content}
        """
                }
            ],
        )

        review_text = response['message']['content']

        if "OK" not in review_text:
            full_review += (
                f"### 📄 Arquivo: `{file_path}`\n"
                f"{review_text}\n\n---\n"
            )

    if full_review != "**Ollama Code Review**\n\n":
        mr.notes.create({'body': full_review})
        print(f"Review comentado no MR #{mr.iid}!")
    else:
        mr.notes.create({'body': "**Ollama Code Review**\n\n Nenhum erro crítico encontrado. "})
        print(
            f"Nada crítico encontrado para o MR #{mr.iid}. Comentário ignorado.")
