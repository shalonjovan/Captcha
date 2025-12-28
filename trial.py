from captcha.captcha import Captcha

c = Captcha(
    captcha_type="text",
    export_format="mp4",
    output_name="text",
    # color_mode="light",
    font_thickness=3,
)

c.generate()
