import gitlab
import ollama

GITLAB_URL = ''
TOKEN = ''
MODELO_OLLAMA = 'reviewer'

gl = gitlab.Gitlab(GITLAB_URL, private_token=TOKEN)

mrs = gl.mergerequests.list(
    assignee_username='joao.demeto',
    state='opened',
    scope='all',
    get_all=True
)

for mr_summary in mrs:
    project = gl.projects.get(mr_summary.project_id)
    mr = project.mergerequests.get(mr_summary.iid)

    print(f"\nAnalisando e comentando no MR #{mr.iid}...")

    changes_data = mr.changes()
    full_review = "**AI Code Review (Staff Engineer Mode)**\n\n"
    for change in changes_data['changes']:
        file_path = change['new_path']
        title = changes_data['title']
        description = changes_data['description']

        if not any(file_path.endswith(ext) for ext in ['.php', '.py', '.sql']):
            continue

        diff_content = change['diff']

        response = ollama.chat(
            model=MODELO_OLLAMA,
            messages=[
                {
                    'role': 'user',
                    'content': f"""
                    File: {file_path}
                    Title: {title}
                    Description: 
                    {description}
                    Full Diff:
                    {diff_content}
                    """
                },
            ]
        )

        review_text = response['message']['content']

        if "OK" not in review_text:
            full_review += (
                f"### 📄 Arquivo: `{file_path}`\n"
                f"{review_text}\n\n---\n"
            )

    if full_review != "**AI Code Review (Staff Engineer Mode)**\n\n":
        mr.notes.create({'body': full_review})
        print(f"Review comentado no MR #{mr.iid}!")
    else:
        print(
            f"Nada crítico encontrado para o MR #{mr.iid}. Comentário ignorado.")
