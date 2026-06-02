"""
天气服务模块
使用wttr.in免费天气API（无需Key）
"""
import requests
import logging

logger = logging.getLogger(__name__)


def get_weather(city_name):
    """
    获取指定城市的实时天气信息（使用wttr.in免费API）
    """
    try:
        # 使用wttr.in免费天气API
        url = f"https://wttr.in/{city_name}?format=j1"
        headers = {'Accept-Language': 'zh-CN'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None, f'查询天气失败（状态码：{response.status_code}）'

        data = response.json()

        # 检查是否查询成功
        if 'current_condition' not in data or not data['current_condition']:
            return None, f'未找到城市: {city_name}'

        current = data['current_condition'][0]

        weather_info = {
            'city': city_name,
            'temp': current.get('temp_C', 'N/A'),
            'feels_like': current.get('FeelsLikeC', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'wind_dir': current.get('winddir16Point', 'N/A'),
            'wind_speed': current.get('windspeedKmph', 'N/A'),
            'description': current.get('lang_zh', [{}])[0].get('value', current.get('weatherDesc', [{}])[0].get('value', 'N/A')),
            'visibility': current.get('visibility', 'N/A'),
            'pressure': current.get('pressure', 'N/A'),
            'uv_index': current.get('uvIndex', 'N/A')
        }

        return weather_info, None

    except requests.exceptions.Timeout:
        return None, '天气查询超时，请稍后重试'
    except requests.exceptions.ConnectionError:
        return None, '网络连接失败，请检查网络'
    except Exception as e:
        logger.error(f"获取天气异常: {str(e)}")
        return None, f'获取天气失败: {str(e)}'


def generate_weather_advice(weather_info):
    """
    根据天气信息生成出行、穿搭、护肤建议
    """
    try:
        temp = int(weather_info['temp'])
    except (ValueError, TypeError):
        temp = 20

    try:
        humidity = int(weather_info['humidity'])
    except (ValueError, TypeError):
        humidity = 50

    description = weather_info.get('description', '')

    try:
        wind_speed = float(weather_info.get('wind_speed', 0))
    except (ValueError, TypeError):
        wind_speed = 0

    advice = {
        '出行建议': [],
        '穿搭建议': [],
        '护肤建议': []
    }

    # ============ 出行建议 ============
    if temp < 0:
        advice['出行建议'].append('天气极寒，尽量减少外出，如需外出请做好全身保暖')
    elif temp < 10:
        advice['出行建议'].append('天气寒冷，外出注意防寒保暖，可适当减少户外活动时间')
    elif temp < 20:
        advice['出行建议'].append('天气凉爽，适合外出活动，早晚温差注意增减衣物')
    elif temp < 30:
        advice['出行建议'].append('天气舒适，非常适合户外活动')
    elif temp < 35:
        advice['出行建议'].append('天气较热，外出注意防暑，避免长时间暴晒')
    else:
        advice['出行建议'].append('高温天气，尽量避免户外活动，注意防暑降温')

    if '雨' in description or '雨' in description:
        advice['出行建议'].append('有雨，记得带伞，注意路面湿滑')
    if '雪' in description:
        advice['出行建议'].append('有雪，注意路滑，驾车注意安全')
    if '雾' in description or '霾' in description:
        advice['出行建议'].append('能见度低，外出建议佩戴口罩，驾车注意安全')
    if wind_speed > 30:
        advice['出行建议'].append('风力较大，注意防风，避免在高楼附近行走')

    # ============ 穿搭建议 ============
    if temp < 5:
        advice['穿搭建议'].append('建议穿羽绒服、棉服，搭配保暖内衣、毛衣，注意头部和手部保暖')
    elif temp < 10:
        advice['穿搭建议'].append('建议穿厚外套、毛衣，可搭配围巾手套')
    elif temp < 15:
        advice['穿搭建议'].append('建议穿薄外套、卫衣，内搭长袖')
    elif temp < 20:
        advice['穿搭建议'].append('建议穿长袖衬衫、薄针织衫，可备一件薄外套')
    elif temp < 25:
        advice['穿搭建议'].append('建议穿短袖、薄长裤，舒适为主')
    elif temp < 30:
        advice['穿搭建议'].append('建议穿短袖、短裤、裙子等清凉衣物')
    else:
        advice['穿搭建议'].append('建议穿轻薄透气衣物，注意防晒')

    if '雨' in description:
        advice['穿搭建议'].append('有雨，建议穿防水鞋，携带雨具')

    # ============ 护肤建议 ============
    if humidity < 30:
        advice['护肤建议'].append('空气干燥，注意保湿补水，建议使用保湿面膜和面霜')
    elif humidity < 50:
        advice['护肤建议'].append('空气较干燥，日常注意保湿，可适当使用保湿喷雾')
    elif humidity > 80:
        advice['护肤建议'].append('空气湿润，注意控油，可使用清爽型护肤品')
    else:
        advice['护肤建议'].append('湿度适中，正常护肤即可')

    if temp > 30:
        advice['护肤建议'].append('高温天气，注意防晒，外出前涂抹防晒霜')
    if temp < 5:
        advice['护肤建议'].append('寒冷天气，注意防冻，可使用滋润型护肤品')

    if '晴' in description and temp > 20:
        advice['护肤建议'].append('天气晴好，紫外线较强，注意防晒')

    return advice


def format_weather_response(weather_info, advice):
    """
    格式化天气响应为文本
    """
    response = f"🌤 **{weather_info['city']}天气**\n\n"
    response += f"🌡 温度: {weather_info['temp']}°C（体感 {weather_info['feels_like']}°C）\n"
    response += f"💧 湿度: {weather_info['humidity']}%\n"
    response += f"🌬 风向: {weather_info['wind_dir']} {weather_info['wind_speed']}km/h\n"
    response += f"☁️ 天气: {weather_info['description']}\n\n"

    for category, items in advice.items():
        if items:
            response += f"**{category}**\n"
            for item in items:
                response += f"• {item}\n"
            response += "\n"

    return response.strip()


# 城市列表
CITY_LIST = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京',
             '重庆', '西安', '苏州', '天津', '长沙', '郑州', '青岛', '大连',
             '厦门', '昆明', '贵阳', '哈尔滨', '长春', '沈阳', '济南', '福州',
             '合肥', '石家庄', '太原', '呼和浩特', '乌鲁木齐', '拉萨',
             '兰州', '银川', '西宁', '海口', '南宁', '南昌', '焦作',
             '洛阳', '开封', '新乡', '许昌', '平顶山', '安阳', '鹤壁',
             '濮阳', '商丘', '信阳', '周口', '驻马店', '漯河', '三门峡',
             '南阳', '焦作', '济源']

# 排除词
EXCLUDE_WORDS = ['今天', '明天', '后天', '现在', '怎么', '什么', '多少', '那个', '这个', '的呢', '呢', '吧', '啊']


def is_weather_query(message):
    """
    判断是否是天气查询
    返回: (is_weather, city_name)
    """
    import re

    # 常见天气关键词
    weather_keywords = ['天气', '气温', '温度', '下雨', '下雪', '晴天', '阴天']

    # 检查是否包含天气关键词
    has_weather_keyword = any(keyword in message for keyword in weather_keywords)

    # 检查是否是省略格式的天气查询（如"焦作的呢"、"那上海呢"）
    # 省略格式：城市名 + 的呢/呢/吧/啊
    omission_pattern = r'^([一-龥]{2,4})(的呢|呢|吧|啊|怎么样|如何|好吗)$'
    omission_match = re.match(omission_pattern, message.strip())

    # 检查是否是"那XX呢"格式
    that_pattern = r'^(那|那|那)([一-龥]{2,4})(的呢|呢|吧|啊|怎么样|如何|好吗)$'
    that_match = re.match(that_pattern, message.strip())

    # 如果是省略格式，检查是否是城市
    if omission_match:
        city = omission_match.group(1)
        if city in CITY_LIST or len(city) >= 2:
            return True, city

    if that_match:
        city = that_match.group(2)
        if city in CITY_LIST or len(city) >= 2:
            return True, city

    # 有天气关键词的情况
    if has_weather_keyword:
        # 尝试提取城市名
        for city in CITY_LIST:
            if city in message:
                return True, city

        # 尝试从消息中提取城市（常见格式）
        patterns = [
            r'([一-龥]{2,4})的?天气',
            r'查询([一-龥]{2,4})天气',
            r'([一-龥]{2,4})今天?天气',
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                city = match.group(1)
                if city not in EXCLUDE_WORDS:
                    return True, city

        return True, None  # 有天气关键词但没找到城市

    return False, None
