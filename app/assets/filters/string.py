from pydantic import StringConstraints

LocaleStr = StringConstraints(pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
