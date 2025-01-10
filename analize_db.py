
from main import *

async def main():
    driver = set_up_driver()
    link = await find_uniswap_link(driver, "0x1f28d8213cda79ce4faa3f0204daadef9385c")
    print(link)
    driver.quit()  # Не забудьте закрити драйвер після виконання

# Запускаємо асинхронну функцію
asyncio.run(main())

