import re

# Refactored pattern
# (?!707070) ensures the following digits aren't the forbidden sequence
REGEX_DISNEY = r"It will expire in 15.*?(?<!#)(?!707070)(\d{6})"

#text = "It will expire in 15 days. Code:                       707070. Real Code: 123456"

text = "passcode to verify the email address associated with your MyDisney account. It will expire in 15 minutes.
                                                                                                                                                        </td>
                                                                                        </tr>
                                                                                        <tr>
                                                                                            <td align="center" style="padding: 25px 45px 25px 45px; font-size: 28px; font-weight: 600; color: #252526; font-family: 'Noto Sans Display', Arial, sans-serif; letter-spacing: 4px; line-height: 38px; mso-line-height-rule: exactly">
                                                                                                                                                            376358
                                                                                                                                                        </td>
                                                                                        </tr>"
match = re.search(REGEX_DISNEY, text)

if match:
    print(match.group(1))  # Output: 123456
