import mysql.connector 
from mysql.connector  import Error
 
def connect_to_database():
    try:
        # 配置数据库连接信息 
        connection = mysql.connector.connect( 
            host="123.249.67.69",       # 数据库服务器地址
            port=3306,                 # 数据库端口（默认为 3306）
            user="fa223797",           # 数据库用户名
            password="Yd011987..",       # 数据库密码
            database="emo"    # 要连接的数据库名称 
        )
 
        if connection.is_connected(): 
            print("成功连接到数据库！")
 
            # 获取数据库版本信息 
            db_info = connection.get_server_info() 
            print(f"数据库版本: {db_info}")
 
            # 创建游标对象
            cursor = connection.cursor() 
 
            # 执行 SQL 查询 
            cursor.execute("SELECT  DATABASE();")
            record = cursor.fetchone() 
            print(f"当前使用的数据库: {record[0]}")
 
    except Error as e:
        print(f"连接数据库时出错: {e}")
 
    finally:
        # 关闭数据库连接
        if connection.is_connected(): 
            cursor.close() 
            connection.close() 
            print("数据库连接已关闭。")
 
# 调用函数
if __name__ == "__main__":
    connect_to_database()