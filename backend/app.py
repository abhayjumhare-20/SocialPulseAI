import os, re
from datetime import datetime, timezone
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import Config
from extensions import db, jwt
from models import User, Analysis, Comment, Recommendation
from platforms import fetch_social, identify_platform
from ml_engine import analyze_comments, make_recommendations, keywords

load_dotenv()
def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=[app.config["FRONTEND_ORIGIN"]])
    db.init_app(app); jwt.init_app(app)
    with app.app_context(): db.create_all()

    def user_id(): return int(get_jwt_identity())
    def analysis_json(a):
        comments=[{"id":c.id,"text":c.text,"sentiment":c.sentiment,"confidence":c.confidence} for c in a.comments]
        recs=[{"problem_title":r.problem_title,"problem_description":r.problem_description,"priority":r.priority,
               "suggested_action":r.suggested_action,"expected_outcome":r.expected_outcome} for r in a.recommendations]
        return {"id":a.id,"url":a.url,"platform":a.platform,"title":a.title,"description":a.description,
                "embed_url":a.media_embed_url,"total_comments":a.total_comments,"positive_count":a.positive_count,
                "negative_count":a.negative_count,"neutral_count":a.neutral_count,"sentiment_score":a.sentiment_score,
                "created_at":a.created_at.isoformat(),"comments":comments,"recommendations":recs,"keywords":keywords(comments)}

    @app.get("/api/health")
    def health(): return jsonify({"status":"ok","service":"SocialPulse AI API"})

    @app.post("/api/auth/register")
    def register():
        d=request.get_json() or {}; name=(d.get("name") or "").strip(); email=(d.get("email") or "").lower().strip(); pw=d.get("password") or ""
        if not name or not email or len(pw)<8: return jsonify(error="Name, valid email and password of at least 8 characters are required."),400
        if User.query.filter_by(email=email).first(): return jsonify(error="Email already registered."),409
        u=User(name=name,email=email); u.set_password(pw); db.session.add(u); db.session.commit()
        token=create_access_token(identity=str(u.id))
        return jsonify(token=token,user={"id":u.id,"name":u.name,"email":u.email,"onboarding_completed":u.onboarding_completed}),201

    @app.post("/api/auth/login")
    def login():
        d=request.get_json() or {}; u=User.query.filter_by(email=(d.get("email") or "").lower().strip()).first()
        if not u or not u.check_password(d.get("password") or ""): return jsonify(error="Invalid email or password."),401
        return jsonify(token=create_access_token(identity=str(u.id)),user={"id":u.id,"name":u.name,"email":u.email,"onboarding_completed":u.onboarding_completed})

    @app.get("/api/auth/profile")
    @jwt_required()
    def profile():
        u=db.session.get(User,user_id())
        return jsonify(id=u.id,name=u.name,email=u.email,language=u.language,theme=u.theme,onboarding_completed=u.onboarding_completed)

    @app.put("/api/settings")
    @jwt_required()
    def settings():
        u=db.session.get(User,user_id()); d=request.get_json() or {}
        if d.get("language") in ("en","hi"): u.language=d["language"]
        if d.get("theme") in ("light","dark"): u.theme=d["theme"]
        if "onboarding_completed" in d: u.onboarding_completed=bool(d["onboarding_completed"])
        db.session.commit()
        return jsonify(language=u.language,theme=u.theme,onboarding_completed=u.onboarding_completed)

    @app.post("/api/analysis/analyze")
    @jwt_required()
    def analyze():
        d=request.get_json() or {}; url=(d.get("url") or "").strip()
        if not re.match(r"^https://",url,re.I): return jsonify(error="Please provide a valid HTTPS social media URL."),400
        try:
            platform=identify_platform(url)
            
            if d.get("demo"):
                demo_comments = [
                    # 40 Positive comments
                    "Amazing work, I really love this!",
                    "Excellent quality and wonderful experience.",
                    "This is absolutely fantastic!",
                    "Great service, very happy with the results.",
                    "I love this product so much.",
                    "Thank you for sharing this amazing content.",
                    "Beautiful work, keep it up!",
                    "Highly recommended to everyone.",
                    "Fantastic experience from start to finish.",
                    "The quality is excellent.",
                    "Really impressed with your work.",
                    "This made my day!",
                    "Superb performance and great results.",
                    "Wonderful product, worth every penny.",
                    "Very helpful and informative post.",
                    "I am completely satisfied with this.",
                    "Amazing customer service!",
                    "One of the best experiences ever.",
                    "Everything was perfect.",
                    "Absolutely love the design.",
                    "Great job, looking forward to more.",
                    "Fast delivery and excellent packaging.",
                    "This is exactly what I wanted.",
                    "Very useful information, thank you.",
                    "Outstanding quality and great value.",
                    "I had a really positive experience.",
                    "Brilliant idea and perfect execution.",
                    "The product works perfectly.",
                    "Really enjoyed watching this.",
                    "Excellent work by the entire team.",
                    "I would definitely recommend this.",
                    "Very pleased with the service.",
                    "This deserves more appreciation.",
                    "Fantastic update, everything works well.",
                    "Loved every moment of this experience.",
                    "Great improvement, keep going!",
                    "The best purchase I have made.",
                    "Beautiful presentation and great details.",
                    "Amazing results, totally worth it.",
                    "Thank you, this is truly wonderful!",

                    # 30 Negative comments
                    "This is terrible and disappointing.",
                    "Very poor quality and bad experience.",
                    "I am extremely unhappy with this.",
                    "Worst service I have ever received.",
                    "Delivery was very late.",
                    "Customer support completely ignored me.",
                    "The product stopped working after one day.",
                    "Very disappointed with the quality.",
                    "This update made everything worse.",
                    "I would not recommend this product.",
                    "The experience was frustrating.",
                    "Poor customer service and no response.",
                    "The price is too expensive for this quality.",
                    "I expected much better results.",
                    "The application keeps crashing.",
                    "Nothing works as promised.",
                    "This was a complete waste of money.",
                    "The product arrived damaged.",
                    "Very slow service and poor communication.",
                    "I regret buying this.",
                    "The quality has become worse.",
                    "I am tired of these repeated problems.",
                    "The delivery experience was awful.",
                    "This feature is full of bugs.",
                    "Not satisfied with the service at all.",
                    "The response time is unacceptable.",
                    "The product does not meet expectations.",
                    "Really bad experience, very disappointing.",
                    "The support team failed to solve my issue.",
                    "I will not purchase this again.",

                    # 30 Neutral comments
                    "What is the price of this product?",
                    "Where can I buy this?",
                    "Please share more details.",
                    "When will this be available?",
                    "Is this available in India?",
                    "Can you explain how it works?",
                    "What are the available options?",
                    "Please provide the website link.",
                    "Is there a different version?",
                    "How long does delivery take?",
                    "What is included in the package?",
                    "Can you share the specifications?",
                    "Where is your store located?",
                    "Does this support Android devices?",
                    "What are the working hours?",
                    "Is registration required?",
                    "Please share the complete details.",
                    "When was this product launched?",
                    "Can I get more information?",
                    "What payment methods are accepted?",
                    "Is this available in other colours?",
                    "How can I contact your team?",
                    "What is the warranty period?",
                    "Can you provide a demonstration?",
                    "Is there a monthly subscription?",
                    "Please tell me the delivery charges.",
                    "What is the next update date?",
                    "Can you share the product catalogue?",
                    "Is this suitable for beginners?",
                    "Where can I find the user guide?"
                ]

                source = {
                    "platform": platform,
                    "title": "Clearly labelled sample analysis (100 demo comments)",
                    "description": "100 predefined synthetic sample comments (40 positive examples, 30 negative examples and 30 neutral examples). These comments were not fetched from the submitted social media post.",
                    "embed_url": "",
                    "comments": demo_comments
                }
            else:
                source = fetch_social(url)

            results=analyze_comments(source["comments"])
            counts={k:sum(1 for c in results if c["sentiment"]==k) for k in ("positive","negative","neutral")}
            total=len(results)
            score=round(((counts["positive"]-counts["negative"])/total)*100,1) if total else 0
            a=Analysis(user_id=user_id(),url=url,platform=source["platform"],title=source.get("title",""),
                       description=source.get("description","")[:5000],media_embed_url=source.get("embed_url",""),
                       total_comments=total,positive_count=counts["positive"],negative_count=counts["negative"],
                       neutral_count=counts["neutral"],sentiment_score=score)
            db.session.add(a); db.session.flush()
            for c in results: db.session.add(Comment(analysis_id=a.id,text=c["text"][:5000],sentiment=c["sentiment"],confidence=c["confidence"]))
            for r in make_recommendations(results): db.session.add(Recommendation(analysis_id=a.id,**r))
            db.session.commit()
            result=analysis_json(a); result["demo"]=bool(d.get("demo"))
            return jsonify(result),201
        except (ValueError,RuntimeError) as e: return jsonify(error=str(e)),400
        except Exception as e:
            app.logger.exception("Analysis failed")
            return jsonify(error="Analysis failed. Check platform access and server logs."),500
    
    @app.post("/api/analysis/manual")
    @jwt_required()
    def analyze_manual():
        d = request.get_json() or {}
        comments = d.get("comments", [])
        title = (d.get("title") or "Manual comment analysis").strip()

        # Accept either a list of comments or multiline text.
        if isinstance(comments, str):
            comments = comments.splitlines()

        if not isinstance(comments, list):
            return jsonify(error="Comments must be provided as a list or text."), 400

        if len(comments) > 500:
            return jsonify(error="You can analyze a maximum of 500 comments at a time."), 400

        cleaned = []
        for item in comments:
            if not isinstance(item, str):
                return jsonify(error="Every comment must be text."), 400
            item = item.strip()
            if item:
                cleaned.append(item[:5000])

        if not cleaned:
            return jsonify(error="Please provide at least one non-empty comment."), 400

        try:
            results = analyze_comments(cleaned)

            counts = {
                key: sum(1 for c in results if c["sentiment"] == key)
                for key in ("positive", "negative", "neutral")
            }

            total = len(results)
            score = round(
                ((counts["positive"] - counts["negative"]) / total) * 100, 1
            ) if total else 0

            analysis = Analysis(
                user_id=user_id(),
                url="manual://comments",
                platform="manual",
                title=title[:200],
                description="Analysis of comments manually pasted or uploaded by the user.",
                media_embed_url="",
                total_comments=total,
                positive_count=counts["positive"],
                negative_count=counts["negative"],
                neutral_count=counts["neutral"],
                sentiment_score=score
            )

            db.session.add(analysis)
            db.session.flush()

            for comment in results:
                db.session.add(Comment(
                    analysis_id=analysis.id,
                    text=comment["text"],
                    sentiment=comment["sentiment"],
                    confidence=comment["confidence"]
                ))

            for recommendation in make_recommendations(results):
                db.session.add(Recommendation(
                    analysis_id=analysis.id,
                    **recommendation
                ))

            db.session.commit()

            response = analysis_json(analysis)
            response["demo"] = False
            response["source"] = "manual"

            return jsonify(response), 201

        except Exception:
            db.session.rollback()
            app.logger.exception("Manual comment analysis failed")
            return jsonify(error="Manual analysis failed. Check the server logs."), 500
    
    @app.get("/api/analysis/history")
    @jwt_required()
    def history():
        items=Analysis.query.filter_by(user_id=user_id()).order_by(Analysis.created_at.desc()).limit(100).all()
        return jsonify([{"id":a.id,"url":a.url,"platform":a.platform,"title":a.title,"total_comments":a.total_comments,
          "positive_count":a.positive_count,"negative_count":a.negative_count,"neutral_count":a.neutral_count,
          "created_at":a.created_at.isoformat()} for a in items])

    @app.get("/api/analysis/<int:aid>")
    @jwt_required()
    def get_analysis(aid):
        a=Analysis.query.filter_by(id=aid,user_id=user_id()).first_or_404()
        return jsonify(analysis_json(a))

    @app.delete("/api/analysis/<int:aid>")
    @jwt_required()
    def delete_analysis(aid):
        a=Analysis.query.filter_by(id=aid,user_id=user_id()).first_or_404()
        db.session.delete(a); db.session.commit()
        return jsonify(message="Analysis deleted.")

    @app.get("/api/analytics/dashboard")
    @jwt_required()
    def dashboard():
        items=Analysis.query.filter_by(user_id=user_id()).all()
        total=sum(a.total_comments for a in items)
        pos=sum(a.positive_count for a in items); neg=sum(a.negative_count for a in items); neu=sum(a.neutral_count for a in items)
        return jsonify(total_analyses=len(items),total_comments=total,positive=pos,negative=neg,neutral=neu,recent=[{"id":a.id,"title":a.title or a.platform,"platform":a.platform,"created_at":a.created_at.isoformat(),"total_comments":a.total_comments} for a in sorted(items,key=lambda x:x.created_at,reverse=True)[:5]])

    @app.post("/api/chatbot/message")
    @jwt_required()
    def chatbot():
        msg=(request.get_json() or {}).get("message","").lower()
        answers=[
          (["sentiment","positive","negative","neutral"],"Sentiment analysis classifies text by emotional polarity: positive, negative, or neutral. Results depend on language, context and model quality."),
          (["url","analyze","link"],"Open New Analysis, paste an HTTPS URL from a supported platform, then choose Analyze. Platform access and comment availability depend on official API permissions."),
          (["graph","chart","percentage"],"The charts summarize the comments successfully retrieved and classified. Demo mode uses synthetic sample comments and is labelled as demo."),
          (["recommend","solution","problem"],"Recommendations are generated from recurring negative-comment keywords and issue categories. Review the supporting comments before acting."),
          (["history","previous","report","pdf"],"Open Analysis History to view previous reports. Select a report to inspect its comments and recommendations."),
          (["youtube"],"YouTube analysis requires a YouTube Data API v3 key in backend/.env. Some videos disable comments or may exceed API quota.")
        ]
        answer=next((a for keys,a in answers if any(k in msg for k in keys)),"I can help with URL analysis, sentiment labels, charts, recommendations, history and reports. Try asking: 'How do I analyze a YouTube URL?'")
        return jsonify(response=answer)

    @app.get("/api/reports/<int:aid>/pdf")
    @jwt_required()
    def pdf_report(aid):
        a=Analysis.query.filter_by(id=aid,user_id=user_id()).first_or_404()
        buf=BytesIO(); c=canvas.Canvas(buf,pagesize=letter); w,h=letter; y=h-50
        c.setFont("Helvetica-Bold",18); c.drawString(45,y,"SocialPulse AI — Analysis Report"); y-=35
        c.setFont("Helvetica",9)
        for line in [f"Analysis ID: {a.id}",f"Platform: {a.platform}",f"URL: {a.url}",f"Title: {a.title[:100]}",
                     f"Date: {a.created_at.isoformat()}",f"Comments analyzed: {a.total_comments}",
                     f"Positive: {a.positive_count} | Negative: {a.negative_count} | Neutral: {a.neutral_count}",
                     f"Sentiment score: {a.sentiment_score}"]:
            c.drawString(45,y,line[:115]); y-=16
        y-=12; c.setFont("Helvetica-Bold",12); c.drawString(45,y,"AI recommendations"); y-=20; c.setFont("Helvetica",9)
        for r in a.recommendations:
            for line in [r.problem_title+" ("+r.priority+")",r.suggested_action,"Expected outcome: "+r.expected_outcome]:
                if y<70: c.showPage(); y=h-50; c.setFont("Helvetica",9)
                c.drawString(45,y,line[:115]); y-=14
            y-=8
        c.save(); buf.seek(0)
        return send_file(buf,mimetype="application/pdf",as_attachment=True,download_name=f"socialpulse-report-{aid}.pdf")

    return app

app=create_app()
if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=os.getenv("FLASK_ENV")=="development")
