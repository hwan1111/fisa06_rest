import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import data_handler as dh  # DB 핸들러 임포트

@st.fragment
def render_party_sidebar(current_user_id: str):
    """
    current_user_id: 로그인한 유저의 DB상 UUID
    """
    # --- 세션 상태 초기화 ---
    if "party_form_open" not in st.session_state:
        st.session_state.party_form_open = False
    if "show_party_options" not in st.session_state:
        st.session_state.show_party_options = False
    if "show_party_list" not in st.session_state:
        st.session_state.show_party_list = False
    
    if "editing_party_id" not in st.session_state:
        st.session_state.editing_party_id = None

    # [수정] st.sidebar.title -> st.title (이미 사이드바 안에 있음)
    st.title("🎉 맛집 원정대")

    # --- 1. 메인 메뉴 토글 ---
    # [수정] st.sidebar.button -> st.button
    if st.button("🍖맛집 원정대 메뉴"):
        st.session_state.show_party_options = not st.session_state.show_party_options
        if not st.session_state.show_party_options:
            st.session_state.party_form_open = False
            st.session_state.show_party_list = False
            st.session_state.editing_party_id = None

    if st.session_state.show_party_options:
        # [수정] st.sidebar.columns -> st.columns
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕원정대 등록"):
                st.session_state.party_form_open = not st.session_state.party_form_open
                if st.session_state.party_form_open:
                    st.session_state.show_party_list = False
                    st.session_state.editing_party_id = None
        with col2:
            if st.button("📋 원정대 목록"):
                st.session_state.show_party_list = not st.session_state.show_party_list
                if st.session_state.show_party_list:
                    st.session_state.party_form_open = False
                    st.session_state.editing_party_id = None

        st.markdown("---")

    # --- 공통 데이터: 맛집 리스트 ---
    restaurants_df = dh.get_all_restaurants()
    rest_map = {}
    if not restaurants_df.empty:
        rest_map = {
            f"{row['name']} ({row['category']})": row['id'] 
            for _, row in restaurants_df.iterrows()
        }
    id_to_name_map = {v: k for k, v in rest_map.items()}

    # --- 2. 원정대 등록 폼 ---
    if st.session_state.get("party_form_open"):
        st.subheader("새 원정대 만들기")
        
        if restaurants_df.empty:
            st.warning("등록된 맛집이 없습니다.")
        else:
            with st.form("party_registration_form"):
                selected_label = st.selectbox("가게 선택", list(rest_map.keys()))
                max_people = st.number_input("모집 인원", 2, 10, 4)
                is_anonymous = st.checkbox("익명 파티 (참여자 이름 숨김)")
                
                if st.form_submit_button("등록 완료"):
                    rest_id = rest_map[selected_label]
                    dh.create_party(rest_id, current_user_id, max_people, is_anonymous)
                    st.success("원정대가 등록되었습니다!")
                    st.session_state.party_form_open = False
                    st.session_state.show_party_list = True
                    st.rerun()

    # --- 3. 원정대 목록 및 상세/수정 ---
    if st.session_state.get("show_party_list"):
        st.subheader("🔥 오늘의 원정대")
        parties_df = dh.get_active_parties()
        
        if not parties_df.empty:
            parties_df['display'] = parties_df.apply(
                lambda x: f"[{x['restaurant_name']}] ({x['current_people']}/{x['max_people']})", axis=1
            )
            party_map = dict(zip(parties_df['display'], parties_df['id']))
            
            selected_display = st.selectbox("참여할 원정대 선택", list(party_map.keys()))
            selected_party_id = party_map[selected_display]
            
            row = parties_df[parties_df['id'] == selected_party_id].iloc[0]
            
            st.markdown("---")

            # === [A] 수정 모드 ===
            is_editing = (st.session_state.editing_party_id == selected_party_id)

            if is_editing:
                st.markdown("### ✏️ 원정대 정보 수정")
                with st.form(key=f"edit_form_{selected_party_id}"):
                    default_rest_label = id_to_name_map.get(row['restaurant_id'])
                    try:
                        default_index = list(rest_map.keys()).index(default_rest_label)
                    except:
                        default_index = 0
                        
                    edit_rest_label = st.selectbox("가게 변경", list(rest_map.keys()), index=default_index)
                    edit_max = st.number_input("인원 변경", 2, 10, value=int(row['max_people']))
                    edit_anon = st.checkbox("익명 여부", value=bool(row['is_anonymous']))
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        if st.form_submit_button("💾 저장"):
                            new_rest_id = rest_map[edit_rest_label]
                            dh.update_party(selected_party_id, new_rest_id, edit_max, edit_anon)
                            st.success("수정되었습니다.")
                            st.session_state.editing_party_id = None
                            st.rerun()
                    with col_e2:
                        if st.form_submit_button("취소"):
                            st.session_state.editing_party_id = None
                            st.rerun()

            else:
                # --- [B] 상세 보기 모드 ---
                st.markdown(f"### 🍽 {row['restaurant_name']}")
                
                # UTC -> KST 시간 변환
                now_utc = datetime.now(timezone.utc)
                now_kst = now_utc + timedelta(hours=9)
                reveal_time = now_kst.replace(hour=12, minute=30, second=0, microsecond=0)
                is_past_reveal_time = now_kst >= reveal_time

                if row['is_anonymous'] and not is_past_reveal_time:
                    host_display = "익명 방장"
                else:
                    host_display = row['host_name']
                
                if row['host_id'] == current_user_id:
                    host_display += " (나)"
                
                st.write(f"👑 **방장:** {host_display}")
                
                if row['is_anonymous']:
                    if is_past_reveal_time:
                        st.caption("🔓 12:30이 지나 명단이 공개되었습니다.")
                    else:
                        st.caption("🔒 12:30에 명단이 공개됩니다.")

                st.write(f"👥 **인원:** {row['current_people']} / {row['max_people']}명")
                st.caption(f"개설: {pd.to_datetime(row['created_at']).strftime('%H:%M')}")

                participants_df = dh.get_party_participants(selected_party_id)
                participant_ids = participants_df['id'].tolist()
                
                display_names = []
                for idx, p_row in participants_df.iterrows():
                    if p_row['id'] == current_user_id:
                        display_names.append(f"{p_row['name']}(나)")
                    elif row['is_anonymous'] and not is_past_reveal_time:
                        display_names.append(f"익명{idx+1}")
                    else:
                        display_names.append(p_row['name'])
                
                st.info("참여자: " + ", ".join(display_names))

                col1, col2 = st.columns(2)
                
                if row['host_id'] == current_user_id:
                    with col1:
                        if st.button("🔧 수정", key=f"edit_btn_{selected_party_id}"):
                            st.session_state.editing_party_id = selected_party_id
                            st.rerun()
                    with col2:
                        if st.button("💣 폭파", key=f"del_btn_{selected_party_id}"):
                            dh.delete_party(selected_party_id)
                            st.warning("원정대가 삭제되었습니다.")
                            st.rerun()
                else:
                    is_joined = current_user_id in participant_ids
                    is_full = row['current_people'] >= row['max_people']

                    with col1:
                        if not is_joined and not is_full:
                            if st.button("✅ 참여하기", key=f"join_{selected_party_id}"):
                                success, msg = dh.join_party(selected_party_id, current_user_id)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                                    
                        elif is_full and not is_joined:
                            st.button("⛔ 만원", disabled=True, key=f"full_{selected_party_id}")
                        elif is_joined:
                            st.button("✅ 참여중", disabled=True, key=f"joined_{selected_party_id}")
                    
                    with col2:
                        if is_joined:
                            if st.button("🏃 나가기", key=f"leave_{selected_party_id}"):
                                dh.leave_party(selected_party_id, current_user_id)
                                st.rerun()
        else:
            st.info("오늘 모집 중인 원정대가 없습니다.")