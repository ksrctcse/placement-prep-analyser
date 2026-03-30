import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './TestPage.css';

const TestPage = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);

  const API_BASE = 'http://localhost:8003';
  const token = localStorage.getItem('access_token');
  const authHeader = `Bearer ${token}`;

  useEffect(() => {
    fetchTest();
  }, [testId]);

  const fetchTest = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/student/test-builder/tests/${testId}`, {
        headers: { 'Authorization': authHeader }
      });
      setTest(response.data);
      
      // Initialize answers object
      const initialAnswers = {};
      response.data.questions.forEach((q, idx) => {
        initialAnswers[idx] = null;
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Error fetching test:', error);
      setError(error.response?.data?.detail || 'Failed to load test');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (questionIndex, option) => {
    setAnswers({
      ...answers,
      [questionIndex]: option
    });
  };

  const handleNext = () => {
    if (currentQuestionIndex < test.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const calculateScore = () => {
    let correctCount = 0;
    test.questions.forEach((question, idx) => {
      if (answers[idx] === question.correct_option) {
        correctCount++;
      }
    });
    return Math.round((correctCount / test.questions.length) * 100);
  };

  const handleSubmit = async () => {
    // Calculate local score for display
    const testScore = calculateScore();
    setScore(testScore);
    setSubmitting(true);
    setSubmitError(null);

    try {
      // Convert quiz answers (index-based) to question ID-based format for backend
      // Only include answered questions (not null/undefined)
      const backendAnswers = {};
      test.questions.forEach((question, idx) => {
        const selectedAnswer = answers[idx];
        // Only include if answer was provided
        if (selectedAnswer) {
          backendAnswers[question.id.toString()] = selectedAnswer;
        }
      });

      const payload = {
        test_id: parseInt(testId),
        answers: backendAnswers,
        time_taken: 0 // Can be enhanced to track actual time spent
      };

      console.log('Submitting test data:', payload);

      const response = await axios.post(
        `${API_BASE}/student/test-builder/submit-test`,
        payload,
        { headers: { 'Authorization': authHeader } }
      );

      console.log('Test submission response:', response.data);
      setSubmissionResult(response.data);
      setSubmitted(true);
    } catch (error) {
      console.error('Error submitting test:', error);
      let errorMessage = 'Failed to submit test. Please try again.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data) {
        // Handle validation errors (422)
        if (Array.isArray(error.response.data)) {
          errorMessage = error.response.data.map(e => e.msg || e.message).join(', ');
        } else {
          errorMessage = JSON.stringify(error.response.data);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setSubmitError(errorMessage);
      setSubmitted(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoBack = () => {
    navigate('/student-dashboard');
  };

  if (loading) {
    return (
      <div className="test-page">
        <div className="loading">Loading test...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="test-page">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button className="btn-back" onClick={handleGoBack}>Go Back to Dashboard</button>
        </div>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="test-page">
        <div className="error-message">Test not found</div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="test-page">
        <div className="results-container">
          {submitError && (
            <div className="error-banner">
              <p><strong>⚠️ Error saving submission:</strong> {submitError}</p>
              <button onClick={() => setSubmitted(false)} className="btn-link">Try again</button>
            </div>
          )}

          <div className="results-header">
            <h1>✅ Test Completed!</h1>
            <p className="test-title">{test.title}</p>
          </div>

          <div className="score-display">
            <div className="score-circle">
              <span className="score-value">{score}%</span>
            </div>
            <div className="score-details">
              <p className="score-text">
                You got <strong>{Math.round((score / 100) * test.total_questions)} out of {test.total_questions}</strong> questions correct
              </p>
              {score >= 70 ? (
                <p className="pass-message">✓ Great job! You passed!</p>
              ) : (
                <p className="fail-message">✗ Try again to improve your score</p>
              )}
            </div>
          </div>

          {submissionResult && (
            <div className="submission-success-banner">
              <p>✨ Your test has been successfully recorded and will appear in your test history.</p>
            </div>
          )}

          <div className="review-section">
            <h3>Review Answers</h3>
            {test.questions.map((question, idx) => (
              <div key={idx} className={`review-item ${answers[idx] === question.correct_option ? 'correct' : 'incorrect'}`}>
                <div className="review-question">
                  <p className="question-num">Q{idx + 1}:</p>
                  <p className="question-text">{question.question_text}</p>
                </div>
                <div className="review-answer">
                  <p>Your answer: <strong>{answers[idx] || 'Not answered'}</strong></p>
                  <p>Correct answer: <strong>{question.correct_option}</strong></p>
                  {answers[idx] !== question.correct_option && question.explanation && (
                    <p className="explanation">Explanation: {question.explanation}</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="results-actions">
            <button className="btn-back" onClick={handleGoBack} disabled={submitting}>
              {submitting ? '⏳ Saving...' : 'Back to Dashboard'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = test.questions[currentQuestionIndex];
  const selectedAnswer = answers[currentQuestionIndex];
  const answeredCount = Object.values(answers).filter(a => a !== null).length;

  return (
    <div className="test-page">
      <div className="test-container">
        <div className="test-header">
          <div className="test-info">
            <h1>{test.title}</h1>
            <p className="question-counter">
              Question {currentQuestionIndex + 1} of {test.total_questions}
            </p>
          </div>
          <div className="test-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${((currentQuestionIndex + 1) / test.total_questions) * 100}%` }}
              ></div>
            </div>
            <p className="progress-text">{answeredCount} of {test.total_questions} answered</p>
          </div>
        </div>

        <div className="question-container">
          <div className="question-content">
            <h3 className="question-text">Q{currentQuestionIndex + 1}: {currentQuestion.question_text}</h3>
            
            <div className="options-list">
              {['A', 'B', 'C', 'D'].map((option) => (
                <label key={option} className="option-item">
                  <input
                    type="radio"
                    name={`question-${currentQuestionIndex}`}
                    value={option}
                    checked={selectedAnswer === option}
                    onChange={() => handleAnswerSelect(currentQuestionIndex, option)}
                  />
                  <span className="option-label">
                    <strong>{option})</strong> {currentQuestion[`option_${option.toLowerCase()}`]}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="navigation-container">
          <button 
            className="btn-nav btn-prev" 
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
          >
            ← Previous
          </button>

          <div className="question-map">
            {test.questions.map((_, idx) => (
              <button
                key={idx}
                className={`question-dot ${idx === currentQuestionIndex ? 'active' : ''} ${answers[idx] ? 'answered' : ''}`}
                onClick={() => setCurrentQuestionIndex(idx)}
                title={`Question ${idx + 1}`}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          {currentQuestionIndex === test.total_questions - 1 ? (
            <button 
              className="btn-submit" 
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? '⏳ Submitting...' : 'Submit Test →'}
            </button>
          ) : (
            <button 
              className="btn-nav btn-next" 
              onClick={handleNext}
            >
              Next →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestPage;
