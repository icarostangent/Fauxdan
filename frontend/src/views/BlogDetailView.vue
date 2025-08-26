<template>
  <div class="blog-detail">
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Loading article...</p>
    </div>

    <div v-else-if="error" class="error">
      <h2>Article Not Found</h2>
      <p>{{ error }}</p>
      <router-link to="/blog" class="back-btn">← Back to Blog</router-link>
    </div>

    <article v-else-if="post" class="post-content">
      <!-- Back Navigation -->
      <div class="back-nav">
        <router-link to="/blog" class="back-link">
          ← Back to Blog
        </router-link>
      </div>

      <!-- Article Header -->
      <header class="post-header">
        <h1>{{ post.title }}</h1>
        <div class="post-meta">
          <div class="meta-left">
            <span class="date">{{ formatDate(post.date) }}</span>
            <span class="read-time">{{ post.readTime }} min read</span>
          </div>
          <div class="tags">
            <span 
              v-for="tag in post.tags" 
              :key="tag" 
              class="tag"
            >
              {{ tag }}
            </span>
          </div>
        </div>
      </header>

      <!-- Article Body -->
      <div class="post-body markdown-content" v-html="renderedContent"></div>

      <!-- Article Footer -->
      <footer class="post-footer">
        <div class="share-section">
          <h3>Share this article</h3>
          <div class="share-buttons">
            <button class="share-btn twitter" @click="shareOnTwitter">
              <span class="share-icon">🐦</span>
              Twitter
            </button>
            <button class="share-btn linkedin" @click="shareOnLinkedIn">
              <span class="share-icon">💼</span>
              LinkedIn
            </button>
            <button class="share-btn copy" @click="copyLink">
              <span class="share-icon">📋</span>
              Copy Link
            </button>
          </div>
        </div>
      </footer>
    </article>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { blogData, BlogPost } from '@/data/blogData'
import { marked } from 'marked'

export default defineComponent({
  name: 'BlogDetailView',
  
  setup() {
    const route = useRoute()
    const loading = ref(true)
    const error = ref('')
    const post = ref<BlogPost | null>(null)
    
    // Render markdown content
    const renderedContent = computed(() => {
      if (!post.value) return ''
      return marked(post.value.content)
    })
    
    const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
    
    const shareOnTwitter = () => {
      const url = encodeURIComponent(window.location.href)
      const text = encodeURIComponent(post.value?.title || '')
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank')
    }
    
    const shareOnLinkedIn = () => {
      const url = encodeURIComponent(window.location.href)
      const title = encodeURIComponent(post.value?.title || '')
      window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank')
    }
    
    const copyLink = async () => {
      try {
        await navigator.clipboard.writeText(window.location.href)
        alert('Link copied to clipboard!')
      } catch (err) {
        console.error('Failed to copy link:', err)
      }
    }
    
    const loadPost = async () => {
      try {
        loading.value = true
        error.value = ''
        const postId = route.params.id as string
        
        const foundPost = await blogData.getPost(postId)
        
        if (foundPost) {
          post.value = foundPost
        } else {
          error.value = 'Article not found'
        }
      } catch (err) {
        error.value = 'Failed to load article'
        console.error('Error loading post:', err)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(() => {
      loadPost()
    })
    
    return {
      loading,
      error,
      post,
      renderedContent,
      formatDate,
      shareOnTwitter,
      shareOnLinkedIn,
      copyLink
    }
  }
})
</script>

<style scoped>
.blog-detail {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
  color: #ffffff;
}

.loading, .error {
  text-align: center;
  padding: 100px 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e9ecef;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 30px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error h2 {
  color: #dc3545;
  margin-bottom: 20px;
  font-size: 28px;
}

.error p {
  color: #6c757d;
  margin-bottom: 30px;
  font-size: 16px;
}

.back-btn, .back-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  font-size: 16px;
  transition: color 0.3s ease;
}

.back-btn:hover, .back-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.back-nav {
  margin-bottom: 40px;
  padding: 20px 0;
  border-bottom: 1px solid #e9ecef;
}

.post-header {
  margin-bottom: 50px;
  text-align: center;
  padding: 40px 0;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  margin: 0 -20px 50px -20px;
}

.post-header h1 {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 30px 0;
  color: #ffffff;
  line-height: 1.2;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.post-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  font-size: 14px;
  color: #6c757d;
}

.meta-left {
  display: flex;
  gap: 20px;
  align-items: center;
}

.date, .read-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
  color: #cccccc;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.tag {
  background: linear-gradient(135deg, #007bff, #8a2be2);
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.post-body {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  margin-bottom: 40px;
  line-height: 1.8;
  color: #ffffff;
}

.post-footer {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.share-section h3 {
  font-size: 20px;
  margin: 0 0 25px 0;
  color: #1a1a1a;
  font-weight: 600;
}

.share-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.share-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
  justify-content: center;
}

.share-icon {
  font-size: 16px;
}

.share-btn.twitter {
  background: #1da1f2;
  color: white;
}

.share-btn.linkedin {
  background: #0077b5;
  color: white;
}

.share-btn.copy {
  background: #6c757d;
  color: white;
}

.share-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Markdown content styling */
.markdown-content {
  font-size: 18px;
  line-height: 1.8;
  color: #ffffff;
  text-align: left;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 40px 0 20px 0;
  color: #ffffff;
  font-weight: 700;
  line-height: 1.3;
}

.markdown-content h1 { 
  font-size: 32px; 
  border-bottom: 3px solid #007bff;
  padding-bottom: 10px;
}

.markdown-content h2 { 
  font-size: 28px; 
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 8px;
}

.markdown-content h3 { 
  font-size: 24px; 
  color: #007bff;
}

.markdown-content h4 { 
  font-size: 20px; 
  color: #cccccc;
}

.markdown-content h5 { 
  font-size: 18px; 
  color: #999999;
}

.markdown-content h6 { 
  font-size: 16px; 
  color: #999999;
}

.markdown-content p {
  margin: 0 0 25px 0;
  text-align: left; /* Change from justify to left */
}

.markdown-content ul,
.markdown-content ol {
  margin: 0 0 25px 0;
  padding-left: 30px;
}

.markdown-content li {
  margin-bottom: 12px;
  line-height: 1.6;
}

.markdown-content blockquote {
  border-left: 4px solid #007bff;
  margin: 30px 0;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0 8px 8px 0;
  font-style: italic;
  font-size: 18px;
  color: #cccccc;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.markdown-content blockquote::before {
  content: '"';
  font-size: 48px;
  color: #007bff;
  float: left;
  margin: -10px 10px 0 -20px;
}

.markdown-content code {
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  color: #00d4aa;
  font-size: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: inline-block;
  vertical-align: baseline;
}

.markdown-content pre {
  background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  color: #e2e8f0;
  padding: 25px;
  border-radius: 12px;
  overflow-x: scroll;
  overflow-y: hidden;
  margin: 30px 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  text-align: left;
  position: relative;
  font-family: 'Fira Code', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre;
  word-wrap: normal;
  min-width: 100%;
}

.markdown-content pre::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #007bff, #8a2be2, #00d4aa);
  border-radius: 12px 12px 0 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: inherit;
  font-size: 14px;
  border: none;
  display: block;
  white-space: pre;
}

/* Custom scrollbar for code blocks */
.markdown-content pre::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.markdown-content pre::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.markdown-content pre::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #007bff, #8a2be2);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.markdown-content pre::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #0056b3, #7b1fa2);
}

/* Firefox scrollbar */
.markdown-content pre {
  scrollbar-width: thin;
  scrollbar-color: #007bff rgba(255, 255, 255, 0.1);
}

.markdown-content a {
  color: #007bff;
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: border-color 0.3s ease;
}

.markdown-content a:hover {
  border-bottom-color: #007bff;
  color: #00d4aa;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  margin: 30px 0;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 30px 0;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.markdown-content th,
.markdown-content td {
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 15px;
  text-align: left;
}

.markdown-content th {
  background: linear-gradient(135deg, #007bff, #8a2be2);
  color: white;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.markdown-content tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.05);
}

.markdown-content tr:hover {
  background: rgba(255, 255, 255, 0.1);
}

.markdown-content hr {
  border: none;
  border-top: 3px solid rgba(255, 255, 255, 0.2);
  margin: 40px 0;
  border-radius: 2px;
}

.markdown-content hr::after {
  content: '◆';
  display: block;
  text-align: center;
  color: #007bff;
  font-size: 20px;
  margin-top: -12px;
  background: #1a1a1a;
  width: 40px;
  margin-left: auto;
  margin-right: auto;
}

@media (max-width: 768px) {
  .blog-detail {
    padding: 15px;
  }
  
  .post-header {
    margin: 0 -15px 40px -15px;
    padding: 30px 20px;
  }
  
  .post-header h1 {
    font-size: 28px;
  }
  
  .post-meta {
    flex-direction: column;
    gap: 15px;
  }
  
  .meta-left {
    flex-direction: column;
    gap: 10px;
  }
  
  .post-body {
    padding: 25px;
  }
  
  .post-footer {
    padding: 25px;
  }
  
  .share-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .share-btn {
    width: 100%;
    max-width: 200px;
  }
  
  .markdown-content {
    font-size: 16px;
  }
  
  .markdown-content h1 { font-size: 24px; }
  .markdown-content h2 { font-size: 22px; }
  .markdown-content h3 { font-size: 20px; }
}
</style>
