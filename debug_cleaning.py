import pandas as pd
from datetime import datetime, timedelta
from app.services.data_cleaning_service import DataCleaningService

# 创建测试数据
test_data = [
    {
        "user_id": "user_1",
        "behavior_type": "click",
        "dish_id": "dish_1",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "user_id": "",
        "behavior_type": "view",
        "dish_id": "dish_2",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "user_id": "user_2",
        "behavior_type": "invalid_type",
        "dish_id": "dish_3",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "user_id": "user_1",
        "behavior_type": "click",
        "dish_id": "dish_1",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "user_id": "user_3",
        "behavior_type": "order",
        "dish_id": "dish_4",
        "timestamp": (datetime.utcnow() - timedelta(days=400)).isoformat()
    }
]

# 调试数据清洗过程
service = DataCleaningService()

# 逐步调试
df = pd.DataFrame(test_data)
print("原始数据:")
print(df)
print()

# 处理缺失值
df = service._handle_missing_values(df)
print("处理缺失值后:")
print(df)
print()

# 处理异常值
df = service._handle_outliers(df)
print("处理异常值后:")
print(df)
print()

# 去重
df = service._remove_duplicates(df)
print("去重后:")
print(df)
print()

# 标准化数据格式
df = service._standardize_data_format(df)
print("标准化数据格式后:")
print(df)
print()

# 验证数据完整性
df = service._validate_data_integrity(df)
print("验证数据完整性后:")
print(df)
print()

# 最终结果
cleaned_data = df.to_dict('records')
print("清洗后的数据:", cleaned_data)
