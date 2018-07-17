class {{ CLS_NAME }}:
    {{ OUTPUT_CLS_NAME }} = namedtuple(
        "{{ OUTPUT_CLS_NAME }}",
        {{ OUTPUTS }},
        module="{{ CLS_NAME }}")

    {% for t in TYPES -%}
    {{ t }} = user_defined_types["{{ t }}"]
    {% endfor %}

    def __init__(self, **kwargs):
        self.__globals = {}

        {% if KWARG_CHECK -%}
        if not kwargs.keys() == {{ CONFIGS }}:
            raise ValueError("Expected kwargs %s. Got %s." %
                             ({{ CONFIGS }}, set(kwargs.keys())))
        {% endif %}

        {% for c in CONFIGS -%}
        self.__globals["{{ c }}"] = kwargs["{{ c }}"]
        {% endfor %}

        {% if ADD_TYPE_CHECKS -%}
        {% for c in CONFIGS -%}
        type_check_input("{{ c }}", self.__globals["{{ c }}"])
        {% endfor %}
        {% endif %}

        {% for r in REGISTERS -%}
        self.__globals["{{ r }}"] = Register("{{ r }}")
        {% endfor %}

        {% for t in TYPES -%}
        self.__globals["{{ t }}"] = {{ CLS_NAME }}.{{ t }}
        {% endfor %}

        self.__globals["__builtins__"] = builtins_

        return

    def __call__(self, **kwargs):

        locals_ = {}

        {% if KWARG_CHECK -%}
        if not kwargs.keys() == {{ DYNAMICS }}:
            raise ValueError("Expected kwargs %s. Got %s." %
                             ({{ DYNAMICS }}, set(kwargs.keys())))
        {% endif %}

        {% for d in DYNAMICS -%}
        locals_["{{ d }}"] = kwargs["{{ d }}"]
        {% endfor %}

        {% if ADD_TYPE_CHECKS -%}
        {% for d in DYNAMICS -%}
        type_check_input("{{ d }}", locals_["{{ d }}"])
        {% endfor %}
        {% endif %}

        exec(module_code, self.__globals, locals_)

        out = {{ CLS_NAME }}.{{ OUTPUT_CLS_NAME }}(
            {% for o in OUTPUTS -%}
            {{ o }}=locals_["{{ o }}"],
            {% endfor %}
        )

        {% for r in REGISTERS -%}
        self.__globals["{{ r }}"].update()
        {% endfor %}

        return out
