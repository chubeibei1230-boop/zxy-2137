import streamlit as st

ROLES = {
    "admin": "管理员",
    "user": "普通用户",
    "auditor": "审计员",
}

ROLE_PERMISSIONS = {
    "admin": {"upload": True, "adjust_threshold": True, "view_report": True, "export": True},
    "user": {"upload": False, "adjust_threshold": True, "view_report": True, "export": True},
    "auditor": {"upload": False, "adjust_threshold": False, "view_report": True, "export": True},
}


def init_auth():
    if "role" not in st.session_state:
        st.session_state.role = "user"


def get_current_role():
    return st.session_state.get("role", "user")


def has_permission(action):
    role = get_current_role()
    return ROLE_PERMISSIONS.get(role, {}).get(action, False)


def render_role_selector():
    role = st.sidebar.selectbox(
        "当前角色",
        options=list(ROLES.keys()),
        format_func=lambda r: ROLES[r],
        index=list(ROLES.keys()).index(get_current_role()),
    )
    if role != st.session_state.role:
        st.session_state.role = role
        st.rerun()

    role_label = ROLES[get_current_role()]
    perms = ROLE_PERMISSIONS[get_current_role()]
    perm_desc = []
    if perms["upload"]:
        perm_desc.append("上传数据")
    if perms["adjust_threshold"]:
        perm_desc.append("调整阈值")
    if perms["view_report"]:
        perm_desc.append("查看报告")
    if perms["export"]:
        perm_desc.append("导出报告")

    st.sidebar.caption(f"权限：{'、'.join(perm_desc)}")
