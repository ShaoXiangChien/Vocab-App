import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid
import random

vocab_df = pd.read_csv("./vocabs.csv")
log_df = pd.read_csv("./quiz_log.csv")
options = ['Main Page', 'Overview', 'Adjustment', 'Quiz']

def upstat(word):
    global vocab_df
    lan = 'English' if 'a' <= word[0] <= 'z' else "Chinese"
    idx = vocab_df[vocab_df[lan] == word].index
    vocab_df.loc[idx, 'Status'] = "learning" if vocab_df[vocab_df[lan] == word].Status.values[0] == "new" else "mastered"
    vocab_df.to_csv("./vocabs.csv", index=False)

def ans_check(submission):
    global vocab_df
    scoring = []
    mistakes = []
    for q, a, s in submission:
        if s in a:
            scoring.append(True)
            upstat(q)
        else:
            scoring.append(False)
            lan = 'English' if q.isalpha() else "Chinese"
            idx = vocab_df[vocab_df[lan] == q].index
            vocab_df.loc[idx, 'Mistake'] += 1
            mistakes.append((q, a))

    score = round(sum(scoring) * 100 / len(scoring), 2)
    return score, mistakes


@st.experimental_memo(suppress_st_warning=True)
def question_gen(test_bank, qnum):
    questions = random.sample(test_bank, qnum)
    for idx, q in enumerate(questions):
        qlan = random.choice(['English', 'Chinese'])
        alan = 'English' if qlan != 'English' else 'Chinese'
        options = [q[alan]] + random.choices(voc_list[alan], k=3)
        random.shuffle(options)
        questions[idx]['qa'] = (q[qlan], q[alan])
        questions[idx]['options'] = options
    return questions








if __name__ == '__main__':
    st.session_state['restart'] = True
    option = st.sidebar.selectbox("Where to go?", options)
    if option == "Main Page":
        st.header("Vocab App for Tiffany")
        st.subheader("Enjoy memorizing vocabs!")
        fig = px.line(log_df['date'].value_counts(), title="Daily Activity")
        fig.update_layout(xaxis_title="date", yaxis_title="quiz count")
        st.plotly_chart(fig)
    elif option == 'Overview':
        st.header(option)
        AgGrid(vocab_df)


    elif option == "Adjustment":
        st.header(option)
        mode = st.radio("Mode", ["Add vocab", "Delete vocab"])
        if mode == "Add vocab":
            num = st.number_input("How many words you want to add?", 1, 200, 5)
            with st.form("Vocabs Adding Form"):
                eng = []
                pos = []
                ch = []
                ei = []
                for i in range(int(num)):
                    col = st.columns(4)
                    eng.append(col[0].text_input("English", key=f"en{i}"))
                    pos.append(col[1].selectbox("POS", ['n.', 'v.', 'adj.', 'adv.',  'phr.', 'conj.', 'pron.'], key=f"sb{i}"))
                    ch.append(col[2].text_input("Chinese", key=f"ch{i}"))
                    ei.append(col[3].text_input("Extra Info", key=f"ei{i}"))
                
                submitted = st.form_submit_button("Add")
                if submitted:
                    tmp = pd.DataFrame({"English": eng, "POS": pos, "Chinese": ch, "Extra Info": ei, "Status": ['new'] * num})
                    vocab_df = pd.concat([vocab_df, tmp], ignore_index=True, axis=0)
                    vocab_df.to_csv("vocabs.csv", index=False)
                    st.success("Vocabs added!")
        else:
            vocab = st.selectbox("Words to delete", vocab_df.English.to_list())
            idx = vocab_df[vocab_df['English'] == vocab].index
            st.write(vocab_df.loc[idx])
            if st.button("Delete"):
                vocab_df = vocab_df.drop(idx)
                st.success(f"{vocab} has been deleted")
                vocab_df.to_csv("./vocabs.csv", index=False)
                
    elif option == "Quiz":
        st.header(option)
        mode = st.radio("Quiz Mode", ['Multiple Choices', 'Short Anwsers'])
        test_bank = [row for _, row in vocab_df.iterrows()]
        voc_list = {'English': vocab_df['English'].to_list(), 'Chinese': vocab_df['Chinese'].to_list()}
        qnum = int(st.number_input("Number of Questions", 5, vocab_df.shape[0], step=5))
        nrow = qnum // 5
        questions = question_gen(test_bank, qnum)
        submission = []

        if mode == "Multiple Choices":
            mcq = st.form("MCQ")
            with mcq:
                # questions = random.sample(test_bank, qnum)
                # submission = []
                for i in range(nrow):
                    cols = st.columns(5)
                    for j in range(5):
                        q = questions[i*5 + j]
                        # qlan = random.choice(['English', 'Chinese'])
                        # alan = 'English' if qlan != 'English' else 'Chinese'
                        # options = [q[alan]] + random.choices(voc_list[alan], k=3)
                        # random.shuffle(options)
                        ans = cols[j].selectbox(q['qa'][0], q['options'])
                        submission.append((q['qa'][0], q['qa'][1], ans))
            
            submitted = mcq.form_submit_button("Submit")
            if submitted:
                result = ans_check(submission)
                tmp = pd.DataFrame({"date": dt.datetime.now().date(), "score": result[0]}, index=[0])
                log_df = pd.concat([log_df, tmp], ignore_index=True, axis=0)
                log_df.to_csv("./quiz_log.csv", index=False)
                st.write(f"Score - {result[0]}")
                if len(result[1]) != 0:
                    st.write("Mistaken words:")
                    for q, a in result[1]:
                        st.write(f"{q} {a}")
        else:
            sa = st.form("Short Anwsers")
            with sa:
                # questions = random.sample(test_bank, qnum)
                # submission = []
                for i in range(nrow):
                    cols = st.columns(5)
                    for j in range(5):
                        q = questions[i*5 + j]
                        # qlan = random.choice(['English', 'Chinese'])
                        # alan = 'English' if qlan != 'English' else 'Chinese'
                        # options = [q[alan]] + random.choices(voc_list[alan], k=3)
                        # random.shuffle(options)
                        ans = cols[j].text_input(q['qa'][0])
                        submission.append((q['qa'][0], q['qa'][1], ans))
            submitted = sa.form_submit_button("Submit")
            if submitted:
                result = ans_check(submission)
                tmp = pd.DataFrame({"date": dt.datetime.now().date(), "score": result[0]}, index=[0])
                log_df = pd.concat([log_df, tmp], ignore_index=True, axis=0)
                log_df.to_csv("./quiz_log.csv", index=False)
                st.write(f"Score - {result[0]}")
                if len(result[1]) != 0:
                    st.write("Mistaken words:")
                    for q, a in result[1]:
                        st.write(f"{q} {a}")
            
            

    

        
        
