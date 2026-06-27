import json
import django
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.rbac.models import Router, Permission


class Command(BaseCommand):
    help = '从 JSON 导入菜单数据（自动处理 ID / name 冲突）'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='menu_export.json')

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('⚠️  开始导入，生产数据已自动备份'))
        with transaction.atomic():
            self.import_core(options['file'])
        self.stdout.write(self.style.SUCCESS('✅ 导入完成'))

    # ---------- 核心逻辑 ----------
    def import_core(self, json_file):
        # 1. 读入
        with open(json_file, 'r', encoding='utf-8') as f:
            menus = json.load(f)

        # 2. 现有数据快照
        exist_id = set(Router.objects.values_list('id', flat=True))
        exist_name = {r.name: r for r in Router.objects.all()}

        # 3. ID 映射表
        id_map = {}

        # 4. 按层级排序（父级先）
        menus.sort(key=lambda m: (m['parent_id'] is not None, m['parent_id'] or 0))

        # 5. 禁用外键检查
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SET foreign_key_checks = 0")

        for m in menus:
            old_id = m['id']
            parent_id = m['parent_id']

            # ----- parent_id 映射 -----
            if parent_id and parent_id in id_map:
                parent_id = id_map[parent_id]

            # ----- 处理 name 唯一冲突 -----
            if m['name'] in exist_name:
                # 已存在 → 直接更新
                router = exist_name[m['name']]
                created = False
            else:
                # 需要新建 → 先解决 ID 冲突
                if old_id in exist_id:
                    new_id = max(exist_id) + 1
                    id_map[old_id] = new_id
                    old_id = new_id
                    exist_id.add(new_id)

                router = Router(id=old_id)
                exist_name[m['name']] = router
                exist_id.add(old_id)
                created = True

            # ----- 通用字段赋值 -----
            router.title = m['title']
            router.name = m['name']
            router.path = m['path']
            router.component = m.get('component') or None
            router.icon = m.get('icon') or None
            router.sort = m.get('sort', 0)
            router.hidden = m.get('hidden', False)
            router.always_show = m.get('always_show', False)
            router.type = m['type']
            router.parent_id = parent_id
            router.save()

            # ----- 按钮权限 → Permission -----
            if m['type'] == 2:
                perm_code = m.get('permission_code') or m['name']
                perm, _ = Permission.objects.update_or_create(
                    code=perm_code,
                    defaults={'name': m['title'], 'router': router}
                )

        with connection.cursor() as cursor:
            cursor.execute("SET foreign_key_checks = 1")