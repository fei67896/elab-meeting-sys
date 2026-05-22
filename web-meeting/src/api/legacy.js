import client from './client'

export const legacyApi = {
  meta() {
    return client.get('/api/legacy/meta')
  },
  sessions(limit = 50) {
    return client.get('/api/legacy/sessions', { params: { limit } })
  },
  students(groupId) {
    return client.get(`/api/legacy/sessions/${groupId}/students`)
  },
  overview(meetingId) {
    return client.get(`/api/legacy/sessions/${meetingId}/overview`)
  },
  series(groupId, studentId, type, maxPoints = 400) {
    return client.get(`/api/legacy/sessions/${groupId}/series`, {
      params: { student_id: studentId, type, max_points: maxPoints },
    })
  },
}
