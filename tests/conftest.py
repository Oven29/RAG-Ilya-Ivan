# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

@pytest.fixture
def sample_arch_query():
    return "Класс UserService выполняет регистрацию пользователя, валидацию и прямое обращение к базе данных"

@pytest.fixture
def sample_trap_query():
    return "Как приготовить борщ с пампушками?"
