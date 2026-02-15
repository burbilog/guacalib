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

- [ ] **1. Дублирование кода SSH tunnel setup**

  **Файлы:** `guacalib/db.py:89-141` и `guacalib/repositories/base.py:244-316`

  Код настройки SSH-туннеля дублируется между фасадом и базовым репозиторием. Нарушает DRY принцип.

  **Рекомендация:** Вынести в отдельный модуль `guacalib/ssh_tunnel.py` или общий метод в `BaseGuacamoleRepository`.

- [ ] **2. Явные commit() в бизнес-логике**

  **Файлы:** `guacalib/cli/handle_conngroup.py:169`, `guacalib/repositories/connection_group.py:327-328`

  ```python
  guacdb.conn.commit()  # Explicit commit внутри репозитория
  ```

  **Проблема:** Нарушает принцип единой транзакции. Context manager должен управлять commit/rollback.

  **Рекомендация:** Убрать явные `commit()` из методов репозиториев, полагаться на `__exit__` context manager.

---

### СРЕДНИЕ

- [ ] **3. Отсутствие type hints в некоторых местах**

  **Файлы:** `guacalib/repositories/connection.py`, `guacalib/repositories/usergroup.py`, `guacalib/repositories/user.py`

  ```python
  def list_users(self):  # Нет return type
  def user_exists(self, username):  # Нет типов аргументов
  ```

  **Рекомендация:** Добавить полные type hints:
  ```python
  def list_users(self) -> List[str]:
  def user_exists(self, username: str) -> bool:
  ```

- [ ] **4. Magic strings для entity types**

  **Файлы:** Многие репозитории

  ```python
  WHERE name = %s AND type = 'USER'
  WHERE type = 'USER_GROUP'
  ```

  **Рекомендация:** Использовать enum или константы:
  ```python
  class EntityType(Enum):
      USER = 'USER'
      USER_GROUP = 'USER_GROUP'
  ```

- [ ] **5. Непоследовательная обработка ошибок в CLI**

  **Файл:** `guacalib/cli/handle_conngroup.py:10-27`

  ```python
  except Exception as e:  # Слишком широкий catch
      guacdb.conn.rollback()  # Прямой доступ к conn
  ```

  **Рекомендация:** Ловить только `GuacalibError` и позволить context manager обрабатывать rollback.

- [ ] **6. Глубокая вложенность SQL-запросов при удалении**

  **Файл:** `guacalib/repositories/user.py:119-174`

  Метод `delete_existing_user` содержит 5 отдельных SQL-запросов с похожей структурой.

  **Рекомендация:** Рассмотреть использование stored procedure или каскадного удаления на уровне БД.

---

### НИЗКИЕ

- [ ] **7. Debug printing смешан с бизнес-логикой**

  **Файл:** `guacalib/repositories/connection_group.py:487-560`

  Метод `debug_connection_permissions` содержит `print()` statements.

  **Рекомендация:** Использовать logging модуль вместо print.

- [ ] **8. Жёстко закодированные значения**

  **Файл:** `guacalib/db.py:113`

  ```python
  "remote_bind_address": (db_config["host"], 3306),  # 3306 hardcoded
  ```

  **Рекомендация:** Вынести в константу или конфигурацию.

- [ ] **9. Неполная валидация параметров**

  **Файл:** `guacalib/repositories/user.py:250-258`

  ```python
  if param_type == "tinyint":
      if param_value not in ("0", "1"):
          # ...
  ```

  Валидация есть только для `tinyint`, но не для `time`, `date`, `string` типов.

  **Рекомендация:** Добавить валидацию для всех типов параметров.

- [ ] **10. Импорты внутри функций (circular import workaround)**

  **Файлы:** `guacalib/db.py:52`, `guacalib/repositories/connection.py:400`

  ```python
  def __init__(self, ...):
      from .repositories.base import BaseGuacamoleRepository
  ```

  **Рекомендация:** Реструктурировать код для избежания circular imports на уровне модулей.

---

## Специфические замечания по файлам

### `guacalib/db.py`

- [ ] **11. Silent exception при закрытии SSH tunnel**

  **Строка:** 171-172

  ```python
  except Exception:
      pass
  ```

  **Рекомендация:** Следует логировать ошибку, а не игнорировать молча.

- [ ] **12. Избыточные статические методы-делегаты**

  **Строки:** 441-460

  Статические методы делегируют в `BaseGuacamoleRepository` - можно использовать class-level import.

### `guacalib/repositories/base.py`

- [ ] **13. Избыточный re-raise**

  **Строки:** 136-139

  ```python
  except (FileNotFoundError, ValueError):
      raise
  ```

  Повторный raise тех же исключений - избыточно.

- [ ] **14. Небезопасное преобразование int()**

  **Строка:** 164

  ```python
  int(os.environ.get("GUACALIB_SSH_TUNNEL_PORT", "22"))
  ```

  Может выбросить `ValueError` если переменная окружения содержит нечисловое значение.

### `guacalib/cli/main.py`

- [ ] **15. Неточный return type**

  **Строка:** 285

  ```python
  def main() -> NoReturn:
  ```

  Функция может завершаться нормально через `sys.exit(0)`, `NoReturn` подразумевает что функция никогда не возвращается.

- [ ] **16. Дублирование except блоков**

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

### `guacalib/cli/handle_conn.py`

- [ ] **17. Глобальные переменные для цветов**

  **Строки:** 16-21

  ```python
  VAR_COLOR = "\033[1;36m"
  RESET = "\033[0m"
  ```

  **Рекомендация:** Лучше использовать класс или константы модуля.

- [ ] **18. Catching generic Exception после специфичных**

  **Строки:** 100-105

  Общий `except Exception` после более специфичных обработчиков.

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
