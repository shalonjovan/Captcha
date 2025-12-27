from captcha.captcha import Captcha

c = Captcha(
    captcha_type="text",
    export_format="gif",
    output_name="demo",
    color_mode="light",
)

c.generate()
