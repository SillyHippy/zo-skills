#!/usr/bin/env python3
import argparse, textwrap
p=argparse.ArgumentParser()
p.add_argument('--task', default='')
args=p.parse_args()
task=args.task.lower()
checks=[]
checks.append('1. Read current user request literally; do not reinterpret.')
checks.append('2. If user requested plan/approval first: STOP after plan until explicit approval.')
checks.append('3. Verify provider/model from authoritative source; do not use proxy output unless proxy explicitly requested.')
checks.append('4. If delivery is Telegram: use Telegram attachment for files; do not trigger email/Resend logic.')
checks.append('5. Do not recommend Meilisearch, local GPU model servers, or extra OCR stacks for this VPS unless explicitly requested.')
checks.append('6. Before claiming done: inspect/test/send-result verification required.')
if 'swarm' in task or 'agent' in task:
    checks.append('7. Agent swarm requires explicit approval and exact provider/model list before execution.')
if 'alibaba' in task or 'coding plan' in task:
    checks.append('8. Alibaba Coding Plan is direct Alibaba Model Studio/Coding Plan only; not Command Code/OpenCode/9router/proxy.')
print('\n'.join(checks))
