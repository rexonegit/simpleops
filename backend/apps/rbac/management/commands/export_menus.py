import json
from django.core.management.base import BaseCommand
from apps.rbac.models import Router


class Command(BaseCommand):
    help = '导出菜单数据为JSON（默认含权限码，--simple 仅菜单）'

    def add_arguments(self, parser):
        parser.add_argument('--simple', action='store_true', help='仅导出菜单，不含权限码')
        parser.add_argument('--output', default='menu_export.json', help='输出文件路径')

    def handle(self, *args, **options):
        simple = options['simple']
        output = options['output']

        menus = Router.objects.all().order_by('parent_id', 'sort')
        data = []

        for menu in menus:
            item = {
                'id': menu.id,
                'parent_id': menu.parent_id,
                'type': menu.type,
                'title': menu.title,
                'name': menu.name,
                'path': menu.path,
                'component': menu.component or '',
                'icon': menu.icon or '',
                'sort': menu.sort,
                'hidden': menu.hidden,
                'always_show': menu.always_show,
            }
            if not simple:
                item['permission_code'] = menu.permission_code if menu.type == 2 else ''
            data.append(item)

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        mode = '仅菜单' if simple else '菜单+权限'
        self.stdout.write(self.style.SUCCESS(f'[{mode}] 导出 {len(data)} 条到 {output}'))
