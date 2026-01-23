import streamlit as st
import pandas as pd
from datetime import datetime
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
    
    # 수정 모드 관리를 위한 세션 변수
    if "editing_party_id" not in st.session_state:
        st.session_state.editing_party_id = None

    st.sidebar.title("🎉 맛집 원정대")

    # --- 1. 메인 메뉴 토글 ---
    if st.sidebar.button("🍖맛집 원정대 메뉴"):
        st.session_state.show_party_options = not st.session_state.show_party_options
        if not st.session_state.show_party_options:
            st.session_state.party_form_open = False
            st.session_state.show_party_list = False
            st.session_state.editing_party_id = None

    if st.session_state.show_party_options:
        col1, col2 = st.sidebar.columns(2)
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

        st.sidebar.markdown("---")

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
        st.sidebar.subheader("새 원정대 만들기")
        
        if restaurants_df.empty:
            st.sidebar.warning("등록된 맛집이 없습니다.")
        else:
            with st.sidebar.form("party_registration_form"):
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
        st.sidebar.subheader("🔥 오늘의 원정대")
        parties_df = dh.get_active_parties()
        
        if not parties_df.empty:
            # 리스트박스용 라벨 생성
            parties_df['display'] = parties_df.apply(
                lambda x: f"[{x['restaurant_name']}] ({x['current_people']}/{x['max_people']})", axis=1
            )
            party_map = dict(zip(parties_df['display'], parties_df['id']))
            
            # 파티 선택
            selected_display = st.sidebar.selectbox("참여할 원정대 선택", list(party_map.keys()))
            selected_party_id = party_map[selected_display]
            
            # 선택된 파티 정보 로드
            row = parties_df[parties_df['id'] == selected_party_id].iloc[0]
            
            st.sidebar.markdown("---")

            # === [A] 수정 모드인지 확인 ===
            is_editing = (st.session_state.editing_party_id == selected_party_id)

            if is_editing:
                # --- 수정 폼 ---
                st.sidebar.markdown("### ✏️ 원정대 정보 수정")
                with st.sidebar.form(key=f"edit_form_{selected_party_id}"):
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
                # --- [B] 일반 상세 보기 모드 ---
                st.sidebar.markdown(f"### 🍽 {row['restaurant_name']}")
                
                # === [추가된 로직] 12:30 자동 공개 ===
                now = datetime.now()
                reveal_time = now.replace(hour=12, minute=30, second=0, microsecond=0)
                is_past_reveal_time = now >= reveal_time

                # 방장 이름 표시
                if row['is_anonymous'] and not is_past_reveal_time:
                    host_display = "익명 방장"
                else:
                    host_display = row['host_name']
                
                if row['host_id'] == current_user_id:
                    host_display += " (나)"
                
                st.sidebar.write(f"👑 **방장:** {host_display}")
                
                # 익명 파티 공개 상태 안내
                if row['is_anonymous']:
                    if is_past_reveal_time:
                        st.sidebar.caption("🔓 12:30이 지나 명단이 공개되었습니다.")
                    else:
                        st.sidebar.caption("🔒 12:30에 명단이 공개됩니다.")

                st.sidebar.write(f"👥 **인원:** {row['current_people']} / {row['max_people']}명")
                st.sidebar.caption(f"개설: {pd.to_datetime(row['created_at']).strftime('%H:%M')}")

                # 참여자 목록 표시
                participants_df = dh.get_party_participants(selected_party_id)
                participant_ids = participants_df['id'].tolist()
                
                display_names = []
                for idx, p_row in participants_df.iterrows():
                    # '나'는 항상 실명으로 표시
                    if p_row['id'] == current_user_id:
                        display_names.append(f"{p_row['name']}(나)")
                    # 익명 파티이고 아직 12:30 전이면 -> 익명 처리
                    elif row['is_anonymous'] and not is_past_reveal_time:
                        display_names.append(f"익명{idx+1}")
                    # 그 외(실명 파티거나 시간이 지났으면) -> 실명 공개
                    else:
                        display_names.append(p_row['name'])
                
                st.sidebar.info("참여자: " + ", ".join(display_names))

                # === 버튼 액션 영역 ===
                col1, col2 = st.sidebar.columns(2)
                
                # 1) 방장인 경우 -> 수정 / 삭제 버튼
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
                
                # 2) 방장이 아닌 경우 -> 참여 / 나가기 버튼
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
            st.sidebar.info("오늘 모집 중인 원정대가 없습니다.")