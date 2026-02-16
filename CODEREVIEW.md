# Code Review: Guacalib Project

**Дата:** 2026-02-15
**Версия:** release/0.24
**Общая оценка:** 8/10

---

## Положительные аспекты (подтверждённые)

- Repository Pattern с базовым классом и специализациями
- Facade Pattern для backward compatibility (GuacamoleDB)
- Context Manager для управления соединениями
- Параметризованные SQL-запросы (защита от SQL injection)
- Password hashing с SHA256 + salt
- Проверка прав доступа конфигурационных файлов (0600)
- Иерархия пользовательских исключений
- Подробная документация параметров

---

## Замечания к исправлению

### КРИТИЧЕСКИЕ

- [x] **1. Дублирование кода SSH tunnel setup** (ИСПРАВЛЕНО)

  **Файлы:** `guacalib/db.py:89-141` и `guacalib/repositories/base.py:244-316`

  Код настройки SSH-туннеля дублируется между фасадом и базовым репозиторием. Нарушает DRY принцип.

  **Решение:** Код вынесен в отдельный модуль `guacalib/ssh_tunnel.py` с функциями `create_ssh_tunnel()` и `close_ssh_tunnel()`. Оба файла теперь используют этот общий модуль.

- [x] **2. Явные commit() в бизнес-логике** (ИСПРАВЛЕНО)

  **Файлы:** `guacalib/cli/handle_conngroup.py:169`, `guacalib/repositories/connection_group.py:327-328`

  ```python
  guacdb.conn.commit()  # Explicit commit внутри репозитория
  ```

  **Проблема:** Нарушает принцип единой транзакции. Context manager должен управлять commit/rollback.

  **Решение:**
  1. Убраны явные `commit()` из `delete_connection_group()` в репозитории и из CLI handlers
  2. Исправлены context managers (`GuacamoleDB.__exit__()` и `BaseGuacamoleRepository.__exit__()`) для корректной обработки `sys.exit()`:
     - `sys.exit(0)` → commit (нормальный выход)
     - `sys.exit(1)` → rollback (выход с ошибкой)
     - Исключения → rollback

---

### СРЕДНИЕ

- [x] **3. Отсутствие type hints в некоторых местах** (ИСПРАВЛЕНО)

  **Файлы:** `guacalib/repositories/connection.py`, `guacalib/repositories/usergroup.py`, `guacalib/repositories/user.py`

  ```python
  def list_users(self):  # Нет return type
  def user_exists(self, username):  # Нет типов аргументов
  ```

  **Решение:** Добавлены полные type hints ко всем публичным методам в указанных файлах:
  - `user.py`: `List[str]`, `bool`, `None`, `Dict[str, List[str]]`
  - `usergroup.py`: `List[str]`, `bool`, `int`, `str`, `None`, `Dict[str, ...]`, `Optional[...]`
  - `connection.py`: `Optional[str]`, `int`, `bool`, `List[str]`, `Tuple[...]`, `None`

  Также исправлен遗漏 (missed) явный `commit()` в `connection.py:delete_existing_connection()`.

- [x] **4. Magic strings для entity types** (ИСПРАВЛЕНО)

  **Файлы:** Многие репозитории

  ```python
  WHERE name = %s AND type = 'USER'
  WHERE type = 'USER_GROUP'
  ```

  **Решение:** Создан модуль `guacalib/entities.py` с enum `EntityType` и константами `ENTITY_TYPE_USER`, `ENTITY_TYPE_USER_GROUP`. Все magic strings заменены на параметризованные запросы с использованием констант:
  - `user.py`: 11 замен
  - `usergroup.py`: 14 замен
  - `connection.py`: 8 замен
  - `connection_group.py`: 5 замен

- [x] **5. Непоследовательная обработка ошибок в CLI** (ИСПРАВЛЕНО)

  **Файл:** `guacalib/cli/handle_conngroup.py:10-27`

  ```python
  except Exception as e:  # Слишком широкий catch
      guacdb.conn.rollback()  # Прямой доступ к conn
  ```

  **Решение:** Удалены все лишние `except Exception` блоки из CLI handlers. Теперь каждый handler ловит только `GuacalibError`, а неожиданные ошибки пробрасываются на верхний уровень в `main.py` где есть общий обработчик.

  Изменены файлы:
  - `handle_conngroup.py`: 4 блока удалено
  - `handle_user.py`: 2 блока удалено, 1 заменён на `GuacalibError`
  - `handle_conn.py`: 4 блока удалено, 2 заменены на `GuacalibError`
  - `handle_dump.py`: 1 блок удалено

- [ ] **6. Глубокая вложенность SQL-запросов при удалении**

  **Файл:** `guacalib/repositories/user.py:119-174`

  Метод `delete_existing_user` содержит 5 отдельных SQL-запросов с похожей структурой.

  **Рекомендация:** Рассмотреть использование stored procedure или каскадного удаления на уровне БД.

---

### НИЗКИЕ

- [x] **7. Debug printing смешан с бизнес-логикой** (ИСПРАВЛЕНО)

  **Файл:** `guacalib/repositories/connection_group.py:487-560`

  Метод `debug_connection_permissions` содержит `print()` statements.

  **Решение:** Заменены все `print()` на `self.debug_print()` для следования существующему паттерну проекта. Теперь вывод контролируется флагом `debug` и не загрязняет stdout в normal режиме.

- [x] **8. Жёстко закодированные значения** (ИСПРАВЛЕНО)

  **Файл:** `guacalib/db.py:113` (теперь `guacalib/ssh_tunnel.py:50`)

  ```python
  "remote_bind_address": (db_config["host"], 3306),  # 3306 hardcoded
  ```

  **Решение:** Добавлена поддержка нестандартного порта MySQL:
  - Константа `DEFAULT_MYSQL_PORT = 3306` как fallback
  - Параметр `remote_port` в конфигурации SSH tunnel
  - Переменная окружения `GUACALIB_SSH_TUNNEL_REMOTE_PORT`
  - Опция `remote_port` в секции `[ssh_tunnel]` конфиг-файла

- [x] **9. Неполная валидация параметров** (ИСПРАВЛЕНО)

  **Файл:** `guacalib/repositories/user.py:250-258`

  ```python
  if param_type == "tinyint":
      if param_value not in ("0", "1"):
          # ...
  ```

  Валидация есть только для `tinyint`, но не для `time`, `date`, `string` типов.

  **Решение:** Добавлена валидация для типов:
  - `tinyint`: 0 или 1 (уже было)
  - `time`: формат HH:MM:SS (добавлено)
  - `date`: формат YYYY-MM-DD (добавлено)
  - `string`: без валидации (произвольная строка)

- [x] **10. Импорты внутри функций (circular import workaround)** (ИСПРАВЛЕНО)

  **Файлы:** `guacalib/db.py:52`, `guacalib/repositories/connection.py:400`

  ```python
  def __init__(self, ...):
      from .repositories.base import BaseGuacamoleRepository
  ```

  **Решение:** После рефакторинга circular imports больше нет. Импорты перенесены на уровень модулей:
  - `db.py`: `BaseGuacamoleRepository` импортирован на верхний уровень
  - `connection.py`: `ConnectionGroupRepository` импортирован на верхний уровень

---

## Специфические замечания по файлам

### `guacalib/db.py`

- [x] **11. Silent exception при закрытии SSH tunnel** (ИСПРАВЛЕНО)

  **Строка:** 171-172 (теперь `guacalib/ssh_tunnel.py:100`)

  ```python
  except Exception:
      pass
  ```

  **Решение:** Добавлено логирование ошибки через `debug_print()` вместо silent pass. Теперь при ошибке закрытия туннеля выводится предупреждение.

- [x] **12. Избыточные статические методы-делегаты** (НЕ ТРЕБУЕТ ИСПРАВЛЕНИЯ)

  **Строки:** 441-460 (теперь 398-411)

  Статические методы делегируют в `BaseGuacamoleRepository` - можно использовать class-level import.

  **Обоснование:** Методы сохранены для backward compatibility API фасада. Пользователи привыкли к `GuacamoleDB.read_config()`. Текущий подход с явными методами лучше чем class-level assignment, потому что сохраняет docstrings для IDE и help().

### `guacalib/repositories/base.py`

- [x] **13. Избыточный re-raise** (ИСПРАВЛЕНО)

  **Строки:** 136-139

  ```python
  except (FileNotFoundError, ValueError):
      raise
  ```

  Повторный raise тех же исключений - избыточно.

  **Решение:** Убран избыточный `except (FileNotFoundError, ValueError): raise`. ValueError теперь пробрасывается автоматически, а другие исключения обёртываются в ValueError с контекстом.

- [x] **14. Небезопасное преобразование int()** (ИСПРАВЛЕНО)

  **Строка:** 164

  ```python
  int(os.environ.get("GUACALIB_SSH_TUNNEL_PORT", "22"))
  ```

  Может выбросить `ValueError` если переменная окружения содержит нечисловое значение.

  **Решение:** Добавлена helper функция `_safe_int()` с понятным сообщением об ошибке. Используется для всех преобразований port и remote_port из переменных окружения и конфиг-файла.

### `guacalib/cli/main.py`

- [ ] **15. Неточный return type**

  **Строка:** 285

  ```python
  def main() -> NoReturn:
  ```

  Функция может завершаться нормально через `sys.exit(0)`, `NoReturn` подразумевает что функция никогда не возвращается.

- [x] **16. Дублирование except блоков** (НЕ ТРЕБУЕТ ИСПРАВЛЕНИЯ)

  **Строки:** 364-366

  Два отдельных except блока с одинаковой логикой:
  ```python
  except GuacalibError as e:
      print(f"Error: {e}")
      sys.exit(1)
  except Exception as e:
      print(f"An error occurred: {e}")
      sys.exit(1)
  ```

  **Обоснование:** Сообщения разные - это правильная практика. `GuacalibError` (ожидаемые бизнес-ошибки) показывают简洁е сообщение, `Exception` (неожиданные ошибки) показывают более развёрнутое сообщение. Это не дублирование, а разные уровни обработки ошибок.

### `guacalib/cli/handle_conn.py`

- [x] **17. Глобальные переменные для цветов** (НЕ ТРЕБУЕТ ИСПРАВЛЕНИЯ)

  **Строки:** 16-21

  ```python
  VAR_COLOR = "\033[1;36m"
  RESET = "\033[0m"
  ```

  **Обоснование:** Текущий подход уже использует "константы модуля" с условной инициализацией при импорте. Они определяются один раз и не изменяются. Использование класса не даёт существенных преимуществ, а добавляет complexity. Текущий код простой и понятный.

- [x] **18. Catching generic Exception после специфичных** (ИСПРАВЛЕНО в п.5)

  **Строки:** 100-105

  Общий `except Exception` после более специфичных обработчиков.

  **Решение:** Исправлено в рамках пункта 5. Все `except Exception` блоки в CLI handlers заменены на `except GuacalibError`.

---

## Рекомендации по улучшению (future work)

- [ ] **19. Добавить logging модуль** вместо print/debug_print
- [ ] **20. Unit-тесты для Python кода** (сейчас только bats для интеграционных тестов)
- [ ] **21. Pre-commit hooks** для автоматической проверки форматирования
- [ ] **22. Type checking с mypy** в CI pipeline
- [ ] **23. Документация API** с Sphinx или pdoc

---

## Соответствие CLAUDE.md

Проект в целом следует guidelines из CLAUDE.md:
- [x] Используются parameterized SQL statements
- [x] Password hashing реализован корректно
- [x] Конфигурационные файлы проверяются на безопасность
- [x] Код структурирован логически

**Отступления:**
- [ ] **24. Длинные функции** - некоторые функции длиннее рекомендованного (например, `handle_conngroup_command` ~350 строк)
- [ ] **25. Неполные type hints** - не все функции имеют полные type hints

---

## Приоритет исправлений

1. **Высокий:** #1, #2 (критические, влияют на поддерживаемость)
2. **Средний:** #3, #4, #5, #6 (качество кода)
3. **Низкий:** #7-18 (улучшения)
4. **Future:** #19-23, #24, #25 (инфраструктурные улучшения)
