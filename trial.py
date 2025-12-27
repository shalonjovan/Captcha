from captcha.captcha import Captcha

c = Captcha(
    captcha_type="noise",
    export_format="gif",
    output_name="demo",
    # color_mode="light",
    font_thickness=3,
)

c.generate()
