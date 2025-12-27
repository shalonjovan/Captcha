from captcha.captcha import Captcha

c = Captcha(
    captcha_type="noise",
    export_format="mp4",
    output_name="demo",
)

c.generate()
