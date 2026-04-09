import pandas as pd
from app.services.data_cleaning_service import DataCleaningService

# 创建测试数据
test_data = [
    {
        "dish_id": "dish_1",
        "merchant_id": "merchant_1",
        "name": "宫保鸡丁",
        "price": 28.5,
        "category": "川菜",
        "sales_volume": 100,
        "rating": 4.5
    },
    {
        "dish_id": "",
        "merchant_id": "merchant_2",
        "name": "麻婆豆腐",
        "price": 22.0,
        "category": "川菜"
    },
    {
        "dish_id": "dish_2",
        "merchant_id": "",
        "name": "水煮鱼",
        "price": 68.0,
        "category": "川菜"
    },
    {
        "dish_id": "dish_3",
        "merchant_id": "merchant_3",
        "name": "糖醋里脊",
        "price": -10.0,
        "category": "鲁菜"
    },
    {
        "dish_id": "dish_4",
        "merchant_id": "merchant_4",
        "name": "红烧肉",
        "price": 9999.0,
        "category": "家常菜"
    },
    {
        "dish_id": "dish_5",
        "merchant_id": "merchant_5",
        "name": "鱼香肉丝",
        "price": 32.0,
        "category": "川菜",
        "rating": 6.0
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
df = service._handle_missing_values(df, is_dish_feature=True)
print("处理缺失值后:")
print(df)
print()

# 处理异常值
df = service._handle_outliers(df, is_dish_feature=True)
print("处理异常值后:")
print(df)
print()

# 去重
df = service._remove_duplicates(df, key_column='dish_id')
print("去重后:")
print(df)
print()

# 标准化数据格式
df = service._standardize_data_format(df, is_dish_feature=True)
print("标准化数据格式后:")
print(df)
print()

# 验证数据完整性
df = service._validate_data_integrity(df, is_dish_feature=True)
print("验证数据完整性后:")
print(df)
print()

# 最终结果
cleaned_data = df.to_dict('records')
print("清洗后的数据:", cleaned_data)
