function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}
function updateRatingDisplay(containerSelector, rating) {
  console.log(
    `[updateRatingDisplay] Called for selector: "${containerSelector}", rating: ${rating}`
  )
  const starsContainer = document.querySelector(containerSelector)
  if (!starsContainer) {
    console.error(
      `[updateRatingDisplay] Container not found for selector: "${containerSelector}"`
    )
    return
  }
  const iconContainers = starsContainer.querySelectorAll(
    '.rating-icon-container'
  )
  console.log(
    `[updateRatingDisplay] Found ${iconContainers.length} icon containers within "${containerSelector}"`
  )
  const ratingValue = parseFloat(rating) || 0
  const fullStars = Math.floor(ratingValue)
  const partialPercentage = (ratingValue - fullStars) * 100
  iconContainers.forEach((container, index) => {
    const filledIcon = container.querySelector('.icon-filled')
    if (!filledIcon) {
      console.warn(
        `[updateRatingDisplay] Filled icon not found in container ${index + 1} for selector "${containerSelector}"`
      )
      return
    }
    let fillWidth = '0%'
    if (index < fullStars) {
      fillWidth = '100%'
    } else if (index === fullStars && partialPercentage > 0) {
      fillWidth = `${partialPercentage}%`
    }
    console.log(
      `[updateRatingDisplay] Setting width ${fillWidth} for icon ${index + 1} in "${containerSelector}"`
    )
    filledIcon.style.width = fillWidth
  })
}
function initializeSimilarRatings() {
  const similarRatingContainers = document.querySelectorAll(
    '.similar-card .similar-card-rating[data-rating]'
  )
  console.log(
    `Found ${similarRatingContainers.length} similar startup rating containers.`
  )
  similarRatingContainers.forEach((container, index) => {
    const ratingStringRaw = container.dataset.rating
    console.log(
      `[Similar Rating] Raw data-rating: "${ratingStringRaw}" for container:`,
      container
    )
    const ratingStringForJs = ratingStringRaw
      ? ratingStringRaw.replace(',', '.')
      : '0'
    const similarRatingValue = parseFloat(ratingStringForJs) || 0
    console.log(
      `[Similar Rating] Processing similar startup card. Parsed rating: ${similarRatingValue}`
    )
    const parentLink = container.closest('.similar-card')
    let uniqueSimilarSelector = null
    if (parentLink && parentLink.getAttribute('href')) {
      uniqueSimilarSelector = `.similar-card[href="${parentLink.getAttribute('href')}"] .similar-card-rating`
    } else {
      console.warn(
        'Could not find unique href for similar card, using index-based selector'
      )
      uniqueSimilarSelector = `.similar-startups-grid .similar-card:nth-child(${index + 1}) .similar-card-rating`
    }
    console.log(`Using selector: ${uniqueSimilarSelector}`)
    if (uniqueSimilarSelector) {
      updateRatingDisplay(uniqueSimilarSelector, similarRatingValue)
    }
  })
}
document.addEventListener('DOMContentLoaded', function () {
  const pageDataElement = document.querySelector('.startup-detail-page')
  if (!pageDataElement) {
    console.error('Не удалось найти основной элемент .startup-detail-page')
    return
  }
  const startupId = pageDataElement.dataset.startupId
  const startupTitle = pageDataElement.dataset.startupTitle
  const isUserAuthenticated =
    pageDataElement.dataset.userAuthenticated === 'true'
  const hasUserVoted = pageDataElement.dataset.userHasVoted === 'true'
  const csrfTokenInput = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  )
  const csrfToken = csrfTokenInput
    ? csrfTokenInput.value
    : getCookie('csrftoken')
  if (!startupId) {
    console.error('Startup ID не найден в data-атрибутах.')
  }
  function updateAnimatedProgressBars(containerElement) {
    if (!containerElement) return
    const visualContainers = containerElement.querySelectorAll(
      '.progress-bar-visual'
    )
    visualContainers.forEach((container) => {
      const animationContainer = container.querySelector(
        '.progress-animation-container'
      )
      const percentageSpan = container.querySelector('.progress-percentage')
      if (animationContainer && percentageSpan) {
        const textContent = percentageSpan.textContent || '0%'
        const progressPercentValue = parseInt(textContent, 10) || 0
        setTimeout(() => {
          animationContainer.style.width = progressPercentValue + '%'
        }, 100)
      } else {
        if (!animationContainer)
          console.error(
            'Animation container (.progress-animation-container) not found in:',
            container
          )
        if (!percentageSpan)
          console.error(
            'Progress text span (.progress-percentage) not found in:',
            container
          )
      }
    })
  }
  const startupDetailPage = document.querySelector('.startup-detail-page')
  updateAnimatedProgressBars(startupDetailPage)
  const ratingDisplayContainer = '.rating-stars[data-rating]'
  const ratingCommentsSelector = '.comment-rating'
  const mainRatingElement = document.querySelector(ratingDisplayContainer)
  if (mainRatingElement) {
    const initialRatingRaw = mainRatingElement.getAttribute('data-rating')
    console.log(`[Main Rating] Raw data-rating: "${initialRatingRaw}"`)
    const ratingStringForJs = initialRatingRaw
      ? initialRatingRaw.replace(',', '.')
      : '0'
    const initialRating = parseFloat(ratingStringForJs)
    console.log(`[Main Rating] Parsed rating value: ${initialRating}`)
    updateRatingDisplay(ratingDisplayContainer, initialRating)
  } else {
    console.error(
      '[Main Rating] Rating container not found with selector:',
      ratingDisplayContainer
    )
  }
  const commentCards = document.querySelectorAll('.comment-card')
  commentCards.forEach((card, cardIndex) => {
    const commentRatingContainer = card.querySelector(ratingCommentsSelector)
    if (
      commentRatingContainer &&
      commentRatingContainer.dataset.rating !== undefined
    ) {
      const commentRatingValue =
        parseFloat(commentRatingContainer.dataset.rating.replace(',', '.')) || 0
      const uniqueCommentSelector = `.comment-card:nth-child(${cardIndex + 1}) ${ratingCommentsSelector}`
      updateRatingDisplay(uniqueCommentSelector, commentRatingValue)
    }
  })
  setTimeout(initializeSimilarRatings, 100)
  const overallRatingStarsElement = document.querySelector(
    '.overall-rating-stars'
  )
  if (overallRatingStarsElement) {
    const overallRatingRaw =
      overallRatingStarsElement.getAttribute('data-rating')
    const overallRatingStringForJs = overallRatingRaw
      ? overallRatingRaw.replace(',', '.')
      : '0'
    const overallRating = parseFloat(overallRatingStringForJs)
    updateRatingDisplay('.overall-rating-stars', overallRating)
  }
  const showMoreCommentsBtn = document.querySelector('.show-more-comments')
  const hideCommentsBtn = document.querySelector('.hide-comments-button')
  const commentsToShow = 5
  if (
    showMoreCommentsBtn &&
    hideCommentsBtn &&
    commentCards.length > commentsToShow
  ) {
    showMoreCommentsBtn.addEventListener('click', function () {
      commentCards.forEach((comment, index) => {
        if (index >= commentsToShow) {
          comment.classList.remove('hidden')
        }
      })
      this.style.display = 'none'
      hideCommentsBtn.style.display = 'inline-flex'
    })
    hideCommentsBtn.addEventListener('click', function () {
      commentCards.forEach((comment, index) => {
        if (index >= commentsToShow) {
          comment.classList.add('hidden')
        }
      })
      this.style.display = 'none'
      showMoreCommentsBtn.style.display = 'inline-flex'
    })
  } else if (showMoreCommentsBtn) {
    showMoreCommentsBtn.style.display = 'none'
  }
  const interactiveStarsContainer = document.querySelector(
    '.rating-stars[data-interactive="true"]'
  )
  if (isUserAuthenticated && !hasUserVoted && interactiveStarsContainer) {
    const iconContainers = interactiveStarsContainer.querySelectorAll(
      '.rating-icon-container[data-value]'
    )
    iconContainers.forEach((iconContainer) => {
      iconContainer.style.cursor = 'pointer'
      iconContainer.addEventListener('click', function () {
        const rating = this.getAttribute('data-value')
        if (!csrfToken) {
          console.error('CSRF токен не найден для голосования.')
          alert(
            'Ошибка: Не удалось выполнить действие. Попробуйте перезагрузить страницу.'
          )
          return
        }
        if (!startupId) {
          console.error('Startup ID не найден для голосования.')
          alert('Ошибка: Не удалось определить стартап.')
          return
        }
        fetch(`/vote-startup/${startupId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: `rating=${rating}`,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              const starsContainerElement = this.closest('.rating-stars')
              if (starsContainerElement) {
                starsContainerElement.removeAttribute('data-interactive')
                starsContainerElement.setAttribute(
                  'data-rating',
                  data.average_rating
                )
                updateRatingDisplay(
                  '.rating-stars[data-rating]',
                  data.average_rating
                )
                starsContainerElement
                  .querySelectorAll('.rating-icon-container')
                  .forEach((container) => {
                    container.removeAttribute('data-value')
                    container.style.cursor = 'default'
                  })
                const ratingValueElement =
                  document.querySelector('.rating-label')
                if (ratingValueElement) {
                  ratingValueElement.textContent = `Рейтинг ${data.average_rating.toFixed(1)}/5`
                }
                const commentAvgRating = document.querySelector(
                  '.average-rating-value'
                )
                if (commentAvgRating) {
                  commentAvgRating.textContent = data.average_rating.toFixed(1)
                }
                const overallRatingStars = document.querySelector(
                  '.overall-rating-stars'
                )
                if (overallRatingStars) {
                  overallRatingStars.setAttribute(
                    'data-rating',
                    data.average_rating
                  )
                  updateRatingDisplay(
                    '.overall-rating-stars',
                    data.average_rating
                  )
                }
              }
            } else {
              alert(data.error || 'Ошибка при голосовании')
            }
          })
          .catch((error) => {
            console.error('Ошибка fetch при голосовании:', error)
            alert('Произошла ошибка сети при голосовании')
          })
      })
      iconContainer.addEventListener('mouseover', function () {
        const value = parseInt(this.getAttribute('data-value'))
        iconContainers.forEach((otherIcon, otherIndex) => {
          const iconFilled = otherIcon.querySelector('.icon-filled')
          if (otherIndex < value) {
            iconFilled.style.width = '100%'
          } else {
            iconFilled.style.width = '0%'
          }
        })
      })
      iconContainer.addEventListener('mouseout', function () {
        const currentRating =
          parseFloat(interactiveStarsContainer.getAttribute('data-rating')) || 0
        iconContainers.forEach((otherIcon, otherIndex) => {
          const iconFilled = otherIcon.querySelector('.icon-filled')
          const value = otherIndex + 1
          if (value <= Math.floor(currentRating)) {
            iconFilled.style.width = '100%'
          } else if (value - 1 < currentRating && currentRating < value) {
            const percentage = (currentRating - Math.floor(currentRating)) * 100
            iconFilled.style.width = `${percentage}%`
          } else {
            iconFilled.style.width = '0%'
          }
        })
      })
    })
  }
  if (typeof GLightbox !== 'undefined') {
    const lightbox = GLightbox({
      selector: '.glightbox',
      loop: true,
      touchNavigation: true,
      keyboardNavigation: true,
      closeOnOutsideClick: true,
      plyr: {
        css: '/static/accounts/libs/plyr/css/plyr.css',
        js: '/static/accounts/libs/plyr/js/plyr.polyfilled.js',
        speed: {
          selected: 1,
          options: [0.5, 1, 1.25, 1.5],
        },
        i18n: {
          restart: 'Перезапустить',
          rewind: 'Перемотать {seektime}с',
          play: 'Воспроизвести',
          pause: 'Пауза',
          fastForward: 'Вперед {seektime}с',
          seek: 'Искать',
          seekLabel: '{currentTime} из {duration}',
          played: 'Воспроизведено',
          buffered: 'Буферизовано',
          currentTime: 'Текущее время',
          duration: 'Продолжительность',
          volume: 'Громкость',
          mute: 'Выключить звук',
          unmute: 'Включить звук',
          enableCaptions: 'Включить субтитры',
          disableCaptions: 'Выключить субтитры',
          download: 'Скачать',
          enterFullscreen: 'Во весь экран',
          exitFullscreen: 'Выйти из полноэкранного режима',
          frameTitle: 'Плеер для {title}',
          captions: 'Субтитры',
          settings: 'Настройки',
          menuBack: 'Назад',
          speed: 'Скорость',
          normal: 'Обычная',
          quality: 'Качество',
          loop: 'Повтор',
          start: 'Старт',
          end: 'Конец',
          all: 'Все',
          reset: 'Сброс',
          disabled: 'Отключено',
          enabled: 'Включено',
          advertisement: 'Реклама',
          qualityBadge: {
            2160: '4K',
            1440: 'HD',
            1080: 'HD',
            720: 'HD',
            576: 'SD',
            480: 'SD',
          },
        },
      },
    })
    console.log('GLightbox initialized with Plyr v3.6.12 and speed options')
  } else {
    console.error(
      'GLightbox is not defined. Check if the library is loaded correctly.'
    )
  }
  const tabContainer = document.querySelector('.tab-navigation')
  const contentSections = document.querySelectorAll('.content-section')
  const tabButtons = document.querySelectorAll('.tab-button')
  if (tabContainer && contentSections.length > 0 && tabButtons.length > 0) {
    tabContainer.addEventListener('click', function (event) {
      const clickedButton = event.target.closest('.tab-button')
      if (clickedButton) {
        const targetId = clickedButton.dataset.target
        if (!targetId) return
        tabButtons.forEach((button) => {
          button.classList.remove('active')
        })
        clickedButton.classList.add('active')
        contentSections.forEach((section) => {
          if (section.id === targetId) {
            section.classList.add('active')
          } else {
            section.classList.remove('active')
          }
        })
      }
    })
  }
  const showMoreSimilarBtn = document.querySelector(
    '.action-button.show-more-similar'
  )
  const similarGrid = document.querySelector('.similar-startups-grid')
  if (showMoreSimilarBtn && similarGrid) {
    showMoreSimilarBtn.addEventListener('click', function () {
      this.textContent = 'Загрузка...'
      this.disabled = true
      const loadSimilarUrl = pageDataElement.dataset.loadSimilarUrl
      if (!loadSimilarUrl) {
        console.error(
          'URL для загрузки похожих стартапов не найден в data-атрибуте!'
        )
        this.innerHTML = '<i class="fas fa-redo"></i> Показать еще'
        this.disabled = false
        alert('Произошла ошибка конфигурации.')
        return
      }
      fetch(loadSimilarUrl)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          return response.text()
        })
        .then((html) => {
          const currentCards = similarGrid.querySelectorAll(
            '.similar-card:not(.show-more-placeholder)'
          )
          currentCards.forEach((card) => card.remove())
          const placeholder = similarGrid.querySelector(
            '.show-more-placeholder'
          )
          if (placeholder) {
            placeholder.insertAdjacentHTML('beforebegin', html)
          } else {
            similarGrid.innerHTML += html
          }
          setTimeout(() => {
            initializeSimilarRatings()
          }, 50)
          this.innerHTML = '<i class="fas fa-redo"></i> Показать еще'
          this.disabled = false
        })
        .catch((error) => {
          console.error('Ошибка при загрузке похожих стартапов:', error)
          this.innerHTML = '<i class="fas fa-redo"></i> Показать еще'
          this.disabled = false
          alert('Не удалось загрузить похожие стартапы.')
        })
    })
  }
  const commentsLink = document.querySelector(
    '.comments-link[href="#comments-section"]'
  )
  const commentsTabButton = document.querySelector(
    '.tab-button[data-target="comments-section"]'
  )
  const commentsSection = document.getElementById('comments-section')
  if (commentsLink && commentsTabButton && commentsSection) {
    commentsLink.addEventListener('click', function (event) {
      event.preventDefault()
      if (!commentsTabButton.classList.contains('active')) {
        commentsTabButton.click()
      }
      if (window.getComputedStyle(commentsSection).display !== 'none') {
        commentsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        const tabContentContainer = document.querySelector(
          '.tab-content-container'
        )
        if (tabContentContainer) {
          const activeSection = tabContentContainer.querySelector(
            '.content-section.active'
          )
          if (activeSection) activeSection.classList.remove('active')
        }
        commentsSection.classList.add('active')
        setTimeout(() => {
          commentsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
      }
    })
  }
  function debounce(func, delay) {
    let timeoutId
    return function (...args) {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => func.apply(this, args), delay)
    }
  }
  function setupUserSearch(modalId, searchInputId, resultsId, onSelect) {
    const searchModalElement = document.getElementById(modalId)
    if (!searchModalElement) return;
    const searchInput = document.getElementById(searchInputId)
    const searchResults = document.getElementById(resultsId)
    const debouncedSearch = debounce(function (query) {
      if (query.length < 2) {
        searchResults.innerHTML = ''
        return
      }
      fetch(`/search-suggestions/?q=${encodeURIComponent(query)}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
      .then(response => response.json())
      .then(data => {
        searchResults.innerHTML = ''
        if (data.suggestions.length === 0) {
          searchResults.innerHTML = '<li class="list-group-item">Пользователи не найдены</li>'
          return
        }
        data.suggestions.forEach(user => {
          const li = document.createElement('li')
          li.classList.add('list-group-item')
          li.style.cursor = 'pointer';
          li.textContent = user.name
          li.dataset.userId = user.id
          li.addEventListener('click', () => {
            onSelect(user);
            if (modalId === 'changeOwnerModal') {
                const currentModal = bootstrap.Modal.getInstance(searchModalElement);
                if (currentModal) {
                    currentModal.hide();
                }
            }
          });
          searchResults.appendChild(li)
        })
      })
      .catch(error => {
        console.error('Ошибка поиска:', error)
        searchResults.innerHTML = '<li class="list-group-item">Ошибка поиска</li>'
      })
    }, 300)
    searchInput.addEventListener('input', function () {
      debouncedSearch(this.value.trim())
    })
    searchModalElement.addEventListener('hidden.bs.modal', function () {
        searchInput.value = '';
        searchResults.innerHTML = '';
    });
  }
  setupUserSearch('changeOwnerModal', 'userSearchInput', 'userSearchResults', (user) => {
    const confirmModalEl = document.getElementById('confirmChangeOwnerModal')
    if (!confirmModalEl) return;
    document.getElementById('newOwnerName').textContent = user.name;
    document.getElementById('newOwnerId').value = user.id;
    const confirmModal = new bootstrap.Modal(confirmModalEl);
    confirmModal.show();
  });
  const confirmChangeOwnerBtn = document.querySelector('.confirm-change-owner')
  if (confirmChangeOwnerBtn) {
    confirmChangeOwnerBtn.addEventListener('click', function () {
      const newOwnerId = document.getElementById('newOwnerId').value
      fetch(`/change_owner/${startupId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: `new_owner_id=${newOwnerId}`,
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('Владелец успешно изменён!')
          location.reload()
        } else {
          alert(data.error || 'Ошибка при смене владельца.')
        }
      })
      .catch(error => {
        console.error('Ошибка:', error)
        alert('Сетевая ошибка при смене владельца.')
      })
    })
  }
  const addInvestorModalEl = document.getElementById('addInvestorModal');
  if (addInvestorModalEl) {
    let selectedInvestor = null;
    setupUserSearch('addInvestorModal', 'investorSearchInput', 'investorSearchResults', (user) => {
      selectedInvestor = user;
      const investorSearchInput = document.getElementById('investorSearchInput');
      investorSearchInput.value = user.name;
      investorSearchInput.disabled = true;
      document.getElementById('investorSearchResults').innerHTML = '';
      document.getElementById('addInvestmentButton').disabled = false;
    });
    const addInvestmentButton = document.getElementById('addInvestmentButton');
    addInvestmentButton.addEventListener('click', function() {
        if (!selectedInvestor) {
            alert('Сначала выберите пользователя из списка.');
            return;
        }
        const amount = document.getElementById('investmentAmount').value;
        if (!amount || parseFloat(amount) <= 0) {
            alert('Введите корректную сумму инвестиции.');
            return;
        }
        fetch(`/add_investor/${startupId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                user_id: selectedInvestor.id,
                amount: amount,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Инвестор успешно добавлен!');
                loadCurrentInvestors();
                resetAddInvestorForm();
                updateStartupFinancials(data.new_amount_raised, data.new_investor_count);
            } else {
                alert(data.error || 'Ошибка при добавлении инвестора.');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Сетевая ошибка при добавлении инвестора.');
        });
    });
    function resetAddInvestorForm() {
        selectedInvestor = null;
        const searchInput = document.getElementById('investorSearchInput');
        searchInput.value = '';
        searchInput.disabled = false;
        document.getElementById('investmentAmount').value = '';
        document.getElementById('addInvestmentButton').disabled = true;
    }
    function loadCurrentInvestors() {
        fetch(`/get_investors/${startupId}/`)
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Ошибка сервера: ${response.status}. Ответ: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const investorsList = document.getElementById('currentInvestorsList');
            investorsList.innerHTML = data.html;
        })
        .catch(error => {
            const investorsList = document.getElementById('currentInvestorsList');
            investorsList.innerHTML = '<p class="text-danger">Не удалось загрузить список инвесторов.</p>';
            console.error('Ошибка загрузки инвесторов:', error)
        });
    }
    document.getElementById('currentInvestorsList').addEventListener('click', function(event) {
        const deleteButton = event.target.closest('.delete-investment-btn');
        if (deleteButton) {
            const userId = deleteButton.dataset.userId;
            if (confirm(`Вы уверены, что хотите удалить этого инвестора?`)) {
                fetch(`/delete_investment/${startupId}/${userId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => { throw new Error(text) });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert('Инвестиция удалена.');
                        loadCurrentInvestors();
                        updateStartupFinancials(data.new_amount_raised, data.new_investor_count);
                    } else {
                        alert(data.error || 'Ошибка при удалении.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при удалении инвестиции:', error);
                    alert('Произошла ошибка при удалении.');
                });
            }
        }
    });
    function updateStartupFinancials(investorCount, amountRaised) {
        console.log('Updating financials:', { investorCount, amountRaised });
        const investorCountDisplay = document.getElementById('investor-count-display');
        if (investorCountDisplay) {
            investorCountDisplay.textContent = `(${investorCount})`;
        } else {
            console.error('Element with id "investor-count-display" not found.');
        }
        const amountRaisedCard = document.querySelector('.info-card-value-button.accent-blue-bg');
        if (amountRaisedCard) {
            amountRaisedCard.textContent = `${new Intl.NumberFormat('ru-RU').format(Math.floor(amountRaised))} ₽`;
        }
        const fundingGoal = parseFloat(pageDataElement.dataset.fundingGoal) || 0;
        const progressPercentage = fundingGoal > 0 ? (amountRaised / fundingGoal) * 100 : 0;
        const progressBar = document.querySelector('.progress-animation-container');
        const progressText = document.querySelector('.progress-percentage');
        if (progressBar) {
            progressBar.style.width = `${Math.min(progressPercentage, 100)}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.floor(progressPercentage)}%`;
        }
    }
    async function loadInvestors() {
    }
    addInvestorModalEl.addEventListener('show.bs.modal', function () {
        loadCurrentInvestors();
        resetAddInvestorForm();
    });
  }
  const submitReportBtn = document.getElementById('submitReport');
  if(submitReportBtn) {
    submitReportBtn.addEventListener('click', function() {
      const reason = document.getElementById('reportReason').value;
      const comment = document.getElementById('reportComment').value;
      if (reason === 'Выберите причину...') {
        alert('Пожалуйста, выберите причину жалобы.');
        return;
      }
      console.log('Жалоба:', { startupId, reason, comment });
      alert('Ваша жалоба отправлена на рассмотрение!');
      const reportModalEl = document.getElementById('reportModal');
      const reportModal = bootstrap.Modal.getInstance(reportModalEl);
      if(reportModal) {
        reportModal.hide();
      }
    });
  }
  const chatButton = document.querySelector('.chat-button');
  if(chatButton && isUserAuthenticated) {
    chatButton.addEventListener('click', function() {
        const ownerId = pageDataElement.dataset.ownerId;
        if (!ownerId) {
            alert('Не удалось определить владельца стартапа.');
            return;
        }
        this.textContent = 'Создание чата...';
        this.disabled = true;
        fetch(`/cosmochat/start-chat/${ownerId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const chatId = data.chat_id || (data.chat && data.chat.conversation_id);
                window.location.href = `/cosmochat/?chat_id=${chatId}`;
            } else {
                alert(data.error || 'Не удалось создать или найти чат.');
                this.textContent = 'Чат';
                this.disabled = false;
            }
        })
        .catch(error => {
            console.error('Ошибка при создании чата:', error);
            alert('Сетевая ошибка. Не удалось создать чат.');
            this.textContent = 'Чат';
            this.disabled = false;
        });
    });
  } else if (chatButton && !isUserAuthenticated) {
    chatButton.addEventListener('click', function() {
        window.location.href = '/login/';
    });
  }
  function setupTruncateText() {
    const charLimit = 256;
    const elements = document.querySelectorAll('.truncatable-text');
    elements.forEach(element => {
      if (element.textContent.trim().length > charLimit) {
        const p = element.querySelector('p');
        if (!p) return;
        const fullText = p.innerHTML;
        const truncatedText = p.textContent.trim().substring(0, charLimit);
        p.innerHTML = `${truncatedText}...`;
        const showMoreButton = document.createElement('button');
        showMoreButton.textContent = 'Показать еще';
        showMoreButton.className = 'action-button show-more-text-button';
        element.appendChild(showMoreButton);
        showMoreButton.addEventListener('click', () => {
          if (showMoreButton.textContent === 'Показать еще') {
            p.innerHTML = fullText;
            showMoreButton.textContent = 'Скрыть';
          } else {
            p.innerHTML = `${truncatedText}...`;
            showMoreButton.textContent = 'Показать еще';
          }
        });
      }
    });
  }
  function setupChatButtons() {
    const ownerId = pageDataElement.dataset.ownerId;
    const userIsAuthenticated = pageDataElement.dataset.userAuthenticated === 'true';
    const handleChatRedirect = async (event) => {
        event.preventDefault();
        if (!userIsAuthenticated) {
            window.location.href = '/login/';
            return;
        }
        if (!ownerId) {
            console.error('Owner ID is not defined.');
            alert('Не удалось определить владельца стартапа.');
            return;
        }
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Создание чата...';
        button.disabled = true;
        try {
            const response = await fetch(`/cosmochat/start-chat/${ownerId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    const chatId = data.chat_id || (data.chat && data.chat.conversation_id);
                    window.location.href = `/cosmochat/?chat_id=${chatId}`;
                } else {
                    console.error('Chat creation failed:', data.error);
                    alert(data.error || 'Не удалось создать чат.');
                    button.textContent = originalText;
                    button.disabled = false;
                }
            } else {
                console.error('Failed to create or find chat', await response.text());
                alert('Произошла ошибка при создании чата.');
                button.textContent = originalText;
                button.disabled = false;
            }
        } catch (error) {
            console.error('Error initiating chat:', error);
            alert('Сетевая ошибка. Не удалось создать чат.');
            button.textContent = originalText;
            button.disabled = false;
        }
    };
    const chatButton = document.querySelector('.chat-button');
    const writeAuthorButton = document.querySelector('.write-author-button');
    if (chatButton) {
      chatButton.addEventListener('click', handleChatRedirect);
    }
    if (writeAuthorButton) {
      writeAuthorButton.addEventListener('click', handleChatRedirect);
    }
  }
  function setupTimelineSteps() {
    const timelineSteps = document.querySelectorAll('.timeline-step');
    const descriptionItems = document.querySelectorAll('.timeline-description-item');
    if (timelineSteps.length === 0 || descriptionItems.length === 0) {
      return;
    }
    timelineSteps.forEach(step => {
      step.addEventListener('click', function() {
        const stepNumber = this.dataset.step;
        descriptionItems.forEach(item => {
          item.classList.remove('active');
        });
        const targetDescription = document.querySelector(`.timeline-description-item:nth-child(${stepNumber})`);
        if (targetDescription) {
          targetDescription.classList.add('active');
          targetDescription.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'start'
          });
        }
        const stepWrapper = this.querySelector('.step-number-wrapper');
        if (stepWrapper) {
          stepWrapper.style.transform = 'scale(0.95)';
          setTimeout(() => {
            stepWrapper.style.transform = '';
          }, 150);
        }
      });
    });
  }
  setupTruncateText();
  setupChatButtons();
  setupTimelineSteps();
  if (pageDataElement) {
    setupRatingStars();
    setupSimilarStartups();
    setupTruncateText();
    setupChatButtons();
    setupTimelineSteps();
    const addInvestorModalEl = document.getElementById('addInvestorModal');
    if (addInvestorModalEl) {
    }
  }
})
