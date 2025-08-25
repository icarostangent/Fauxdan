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
          <span class="date">{{ formatDate(post.date) }}</span>
          <span class="read-time">{{ post.readTime }} min read</span>
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
              Twitter
            </button>
            <button class="share-btn linkedin" @click="shareOnLinkedIn">
              LinkedIn
            </button>
            <button class="share-btn copy" @click="copyLink">
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
        // You could add a toast notification here
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
}

.loading, .error {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error h2 {
  color: #dc3545;
  margin-bottom: 20px;
}

.back-btn, .back-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.back-btn:hover, .back-link:hover {
  text-decoration: underline;
}

.back-nav {
  margin-bottom: 30px;
}

.post-header {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 2px solid #e9ecef;
}

.post-header h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 20px 0;
  color: #1a1a1a;
  line-height: 1.2;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  font-size: 14px;
  color: #6c757d;
  flex-wrap: wrap;
}

.tags {
  display: flex;
  gap: 8px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.post-body {
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 60px;
}

.post-footer {
  border-top: 2px solid #e9ecef;
  padding-top: 30px;
}

.share-section h3 {
  font-size: 18px;
  margin: 0 0 20px 0;
  color: #1a1a1a;
}

.share-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.share-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
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
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

/* Markdown content styling */
.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 30px 0 15px 0;
  color: #1a1a1a;
  font-weight: 600;
}

.markdown-content h1 { font-size: 28px; }
.markdown-content h2 { font-size: 24px; }
.markdown-content h3 { font-size: 20px; }
.markdown-content h4 { font-size: 18px; }
.markdown-content h5 { font-size: 16px; }
.markdown-content h6 { font-size: 14px; }

.markdown-content p {
  margin: 0 0 20px 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 0 0 20px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin-bottom: 10px;
}

.markdown-content blockquote {
  border-left: 4px solid #007bff;
  margin: 20px 0;
  padding: 10px 20px;
  background: #f8f9fa;
  font-style: italic;
}

.markdown-content code {
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  color: #e83e8c;
  font-size: 14px;
}

.markdown-content pre {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 20px 0;
  border: 1px solid #e9ecef;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  color: #333;
  font-size: 14px;
}

.markdown-content a {
  color: #007bff;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 20px 0;
}

.markdown-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #dee2e6;
  padding: 12px;
  text-align: left;
}

.markdown-content th {
  background: #f8f9fa;
  font-weight: 600;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #dee2e6;
  margin: 30px 0;
}

@media (max-width: 768px) {
  .post-header h1 {
    font-size: 28px;
  }
  
  .post-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .share-buttons {
    flex-direction: column;
  }
  
  .share-btn {
    width: 100%;
  }
}
</style>
